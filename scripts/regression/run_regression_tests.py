import argparse
import asyncio
import csv
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ingestion import parser as ingestion_parser
from backend.app.services.ingestion.cleaner import clean_text


DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "regression" / "corpus"
DEFAULT_MARKDOWN_REPORT = ROOT_DIR / "docs" / "regression" / "regression_test_report.md"
DEFAULT_CSV_REPORT = ROOT_DIR / "docs" / "regression" / "regression_results.csv"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".xlsx"}
PRODUCTION_INGESTION_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".xlsx"}
EXPECTED_SUFFIX = ".expected.json"


@dataclass
class OcrMetrics:
    fallback_triggered: bool = False
    processing_time_seconds: Optional[float] = None
    confidence: Optional[float] = None
    scanned_pdf_detected: bool = False
    error: Optional[str] = None


@dataclass
class RegressionResult:
    file: Path
    expected_file: Optional[Path]
    expected: Dict[str, Any] = field(default_factory=dict)
    actual: Dict[str, Any] = field(default_factory=dict)
    passed: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    parse_time_seconds: float = 0.0
    analysis_time_seconds: float = 0.0
    text_char_count: int = 0
    ocr: OcrMetrics = field(default_factory=OcrMetrics)
    error: Optional[str] = None

    @property
    def relative_file(self) -> str:
        try:
            return str(self.file.relative_to(ROOT_DIR))
        except ValueError:
            return str(self.file)


class OcrLogCapture(logging.Handler):
    def __init__(self, metrics: OcrMetrics):
        super().__init__()
        self.metrics = metrics

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        confidence_match = re.search(r"OCR confidence:\s*([\d.]+)%", message)
        if confidence_match:
            self.metrics.confidence = float(confidence_match.group(1)) / 100.0
        duration_match = re.search(r"OCR duration:\s*([\d.]+)\s*seconds", message)
        if duration_match:
            self.metrics.processing_time_seconds = float(duration_match.group(1))


def discover_documents(corpus_dir: Path) -> List[Path]:
    return sorted(
        path
        for path in corpus_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.endswith(EXPECTED_SUFFIX)
    )


def expected_path_for(document_path: Path) -> Path:
    return document_path.with_suffix(".expected.json")


def load_expected(expected_path: Path) -> Dict[str, Any]:
    with expected_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_scanned_pdf(path: Path, expected: Dict[str, Any]) -> bool:
    if path.suffix.lower() != ".pdf":
        return False
    if expected.get("format") in {"scanned_pdf", "ocr_noisy_pdf"}:
        return True
    try:
        reader = PdfReader(path)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        return len(extracted.strip()) < 50
    except Exception:
        return True


def parse_with_production_ingestion(path: Path, expected: Dict[str, Any], result: RegressionResult) -> str:
    result.ocr.scanned_pdf_detected = detect_scanned_pdf(path, expected)

    if path.suffix.lower() not in PRODUCTION_INGESTION_EXTENSIONS:
        raise ValueError(f"Unsupported production ingestion extension: {path.suffix}")

    original_ocr = ingestion_parser.parse_pdf_ocr
    logger = logging.getLogger("governance_copilot.ingestion.parser")
    log_capture = OcrLogCapture(result.ocr)

    def wrapped_ocr(pdf_path: Path) -> str:
        result.ocr.fallback_triggered = True
        start = time.perf_counter()
        try:
            return original_ocr(pdf_path)
        except Exception as exc:
            result.ocr.error = str(exc)
            raise
        finally:
            elapsed = time.perf_counter() - start
            if result.ocr.processing_time_seconds is None:
                result.ocr.processing_time_seconds = elapsed

    ingestion_parser.parse_pdf_ocr = wrapped_ocr
    logger.addHandler(log_capture)
    try:
        return ingestion_parser.parse_file(str(path), path.suffix.lstrip(".").lower())
    finally:
        logger.removeHandler(log_capture)
        ingestion_parser.parse_pdf_ocr = original_ocr


async def analyze_text(text: str) -> Dict[str, Any]:
    service = AIService()
    return await service.analyze_governance_document(clean_text(text), context="")


def _count(actual: Dict[str, Any], key: str) -> int:
    value = actual.get(key, [])
    return len(value) if isinstance(value, list) else 0


def validate_result(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    failures = []

    if expected.get("document_type") and actual.get("document_type") != expected["document_type"]:
        failures.append(
            f"document_type expected {expected['document_type']}, actual {actual.get('document_type')}"
        )

    if expected.get("governance_relevance") and actual.get("governance_relevance") != expected["governance_relevance"]:
        failures.append(
            "governance_relevance expected "
            f"{expected['governance_relevance']}, actual {actual.get('governance_relevance')}"
        )

    threshold_specs = [
        ("raid_items", "raid_items_min", ">="),
        ("raid_items", "raid_items_max", "<="),
        ("escalation_items", "escalations_min", ">="),
        ("escalation_items", "escalations_max", "<="),
        ("meeting_actions", "meeting_actions_min", ">="),
        ("meeting_actions", "meeting_actions_max", "<="),
    ]
    for actual_key, expected_key, operator in threshold_specs:
        if expected_key not in expected:
            continue
        actual_count = _count(actual, actual_key)
        expected_value = int(expected[expected_key])
        if operator == ">=" and actual_count < expected_value:
            failures.append(f"{actual_key} expected >= {expected_value}, actual {actual_count}")
        if operator == "<=" and actual_count > expected_value:
            failures.append(f"{actual_key} expected <= {expected_value}, actual {actual_count}")

    return failures


async def process_document(path: Path, index: int, total: int) -> RegressionResult:
    print(f"[{index}/{total}] Processing {path.name}")
    expected_path = expected_path_for(path)
    result = RegressionResult(file=path, expected_file=expected_path if expected_path.exists() else None)
    start = time.perf_counter()

    try:
        if not expected_path.exists():
            raise FileNotFoundError(f"Missing expected JSON: {expected_path.name}")

        result.expected = load_expected(expected_path)

        parse_start = time.perf_counter()
        text = parse_with_production_ingestion(path, result.expected, result)
        result.parse_time_seconds = time.perf_counter() - parse_start
        result.text_char_count = len(text)

        analysis_start = time.perf_counter()
        result.actual = await analyze_text(text)
        result.analysis_time_seconds = time.perf_counter() - analysis_start

        result.failure_reasons = validate_result(result.expected, result.actual)
        result.passed = not result.failure_reasons
    except Exception as exc:
        result.error = str(exc)
        result.failure_reasons = [str(exc)]
        result.passed = False
    finally:
        result.processing_time_seconds = time.perf_counter() - start

    if result.passed:
        print(f"PASS:\n{path.name}\n")
    else:
        print(f"FAIL:\n{path.name}\n")
        for reason in result.failure_reasons:
            expected_msg, actual_msg = split_failure_reason(reason)
            print(f"Expected:\n{expected_msg}\n")
            print(f"Actual:\n{actual_msg}\n")

    return result


def split_failure_reason(reason: str) -> tuple[str, str]:
    threshold = re.match(r"(\w+) expected ([<>]= \d+), actual (\d+)", reason)
    if threshold:
        return f"{threshold.group(1)} {threshold.group(2)}", f"{threshold.group(1)} = {threshold.group(3)}"
    if " expected " in reason and ", actual " in reason:
        left, actual = reason.split(", actual ", 1)
        field, expected = left.split(" expected ", 1)
        return f"{field} = {expected}", f"{field} = {actual}"
    return reason, "See failure reason"


def compute_metrics(results: List[RegressionResult]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed
    with_actual = [result for result in results if result.actual]

    def expected_positive(result: RegressionResult, key: str) -> bool:
        return int(result.expected.get(key, 0) or 0) > 0

    classification_correct = sum(
        1 for result in with_actual
        if result.expected.get("document_type") == result.actual.get("document_type")
    )
    governance_correct = sum(
        1 for result in with_actual
        if result.expected.get("governance_relevance") == result.actual.get("governance_relevance")
    )

    governance_expected_positive = [
        result for result in with_actual
        if result.expected.get("governance_relevance") in {"medium", "high"}
    ]
    governance_actual_positive = [
        result for result in with_actual
        if result.actual.get("governance_relevance") in {"medium", "high"}
    ]
    governance_true_positive = [
        result for result in with_actual
        if result.expected.get("governance_relevance") in {"medium", "high"}
        and result.actual.get("governance_relevance") in {"medium", "high"}
    ]

    raid_expected = [result for result in with_actual if expected_positive(result, "raid_items_min")]
    raid_hits = [
        result for result in raid_expected
        if _count(result.actual, "raid_items") >= int(result.expected.get("raid_items_min", 0))
    ]

    escalation_expected_zero = [
        result for result in with_actual
        if int(result.expected.get("escalations_max", 999999)) == 0
    ]
    escalation_false_positive = [
        result for result in escalation_expected_zero
        if _count(result.actual, "escalation_items") > 0
    ]

    meeting_expected = [result for result in with_actual if expected_positive(result, "meeting_actions_min")]
    meeting_hits = [
        result for result in meeting_expected
        if _count(result.actual, "meeting_actions") >= int(result.expected.get("meeting_actions_min", 0))
    ]

    ocr_expected = [result for result in results if result.ocr.fallback_triggered]
    ocr_success = [
        result for result in ocr_expected
        if result.ocr.fallback_triggered and result.text_char_count > 0 and not result.ocr.error
    ]

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_percent": (passed / total * 100) if total else 0.0,
        "classification_accuracy": (classification_correct / len(with_actual) * 100) if with_actual else 0.0,
        "governance_detection_accuracy": (governance_correct / len(with_actual) * 100) if with_actual else 0.0,
        "governance_precision": (len(governance_true_positive) / len(governance_actual_positive) * 100) if governance_actual_positive else 0.0,
        "governance_recall": (len(governance_true_positive) / len(governance_expected_positive) * 100) if governance_expected_positive else 0.0,
        "raid_extraction_recall": (len(raid_hits) / len(raid_expected) * 100) if raid_expected else 0.0,
        "escalation_false_positive_rate": (len(escalation_false_positive) / len(escalation_expected_zero) * 100) if escalation_expected_zero else 0.0,
        "meeting_action_recall": (len(meeting_hits) / len(meeting_expected) * 100) if meeting_expected else 0.0,
        "ocr_success_rate": (len(ocr_success) / len(ocr_expected) * 100) if ocr_expected else 0.0,
        "ocr_expected": len(ocr_expected),
        "ocr_success": len(ocr_success),
        "with_actual": len(with_actual),
    }


def confusion_summary(results: List[RegressionResult]) -> Dict[str, Counter]:
    classification = Counter()
    governance = Counter()
    for result in results:
        if not result.actual:
            continue
        classification[(result.expected.get("document_type"), result.actual.get("document_type"))] += 1
        governance[(result.expected.get("governance_relevance"), result.actual.get("governance_relevance"))] += 1
    return {"classification": classification, "governance": governance}


def categorize_failure(reason: str) -> str:
    if "Production ingestion does not currently support XLSX" in reason:
        return "unsupported_ingestion_format"
    if "document_type expected" in reason:
        return "classification_mismatch"
    if "governance_relevance expected" in reason:
        return "governance_relevance_mismatch"
    if "raid_items expected" in reason:
        return "raid_extraction_threshold"
    if "escalation_items expected" in reason:
        return "escalation_threshold"
    if "meeting_actions expected" in reason:
        return "meeting_action_threshold"
    if "OCR" in reason or "ocr" in reason:
        return "ocr_failure"
    return "other"


def write_csv(results: List[RegressionResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "file", "passed", "failure_reasons", "expected_document_type", "actual_document_type",
        "expected_governance_relevance", "actual_governance_relevance", "raid_items",
        "escalation_items", "meeting_actions", "ocr_fallback_triggered",
        "scanned_pdf_detected", "ocr_processing_time_seconds", "ocr_confidence",
        "processing_time_seconds", "parse_time_seconds", "analysis_time_seconds",
        "text_char_count",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "file": result.relative_file,
                "passed": result.passed,
                "failure_reasons": " | ".join(result.failure_reasons),
                "expected_document_type": result.expected.get("document_type"),
                "actual_document_type": result.actual.get("document_type"),
                "expected_governance_relevance": result.expected.get("governance_relevance"),
                "actual_governance_relevance": result.actual.get("governance_relevance"),
                "raid_items": _count(result.actual, "raid_items"),
                "escalation_items": _count(result.actual, "escalation_items"),
                "meeting_actions": _count(result.actual, "meeting_actions"),
                "ocr_fallback_triggered": result.ocr.fallback_triggered,
                "scanned_pdf_detected": result.ocr.scanned_pdf_detected,
                "ocr_processing_time_seconds": result.ocr.processing_time_seconds,
                "ocr_confidence": result.ocr.confidence,
                "processing_time_seconds": round(result.processing_time_seconds, 3),
                "parse_time_seconds": round(result.parse_time_seconds, 3),
                "analysis_time_seconds": round(result.analysis_time_seconds, 3),
                "text_char_count": result.text_char_count,
            })


def write_markdown(results: List[RegressionResult], metrics: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failure_categories = Counter()
    for result in results:
        for reason in result.failure_reasons:
            failure_categories[categorize_failure(reason)] += 1

    confusions = confusion_summary(results)
    failed_results = [result for result in results if not result.passed]
    ocr_failures = [
        result for result in results
        if result.ocr.error or (result.ocr.fallback_triggered and result.text_char_count == 0)
    ]
    scanned_without_ocr = [
        result for result in results
        if result.ocr.scanned_pdf_detected and not result.ocr.fallback_triggered and result.text_char_count > 0
    ]
    false_escalations = [
        result for result in results
        if int(result.expected.get("escalations_max", 999999)) == 0
        and _count(result.actual, "escalation_items") > 0
    ]
    raid_misses = [
        result for result in results
        if int(result.expected.get("raid_items_min", 0) or 0) > _count(result.actual, "raid_items")
    ]

    lines = [
        "# Enterprise Regression Test Report",
        "",
        "## Summary",
        "",
        f"- Total files: {metrics['total']}",
        f"- Total passed: {metrics['passed']}",
        f"- Total failed: {metrics['failed']}",
        f"- Pass percent: {metrics['pass_percent']:.2f}%",
        "",
        "## Metrics",
        "",
        f"- Classification Accuracy: {metrics['classification_accuracy']:.2f}%",
        f"- Governance Detection Accuracy: {metrics['governance_detection_accuracy']:.2f}%",
        f"- Governance Precision: {metrics['governance_precision']:.2f}%",
        f"- Governance Recall: {metrics['governance_recall']:.2f}%",
        f"- RAID Extraction Recall: {metrics['raid_extraction_recall']:.2f}%",
        f"- Escalation False Positive Rate: {metrics['escalation_false_positive_rate']:.2f}%",
        f"- Meeting Action Recall: {metrics['meeting_action_recall']:.2f}%",
        f"- OCR Success Rate: {metrics['ocr_success_rate']:.2f}%",
        "",
        "## Top Failure Categories",
        "",
    ]
    if failure_categories:
        lines.extend(f"- {category}: {count}" for category, count in failure_categories.most_common())
    else:
        lines.append("- None")

    lines.extend(["", "## Failed Documents", ""])
    if failed_results:
        for result in failed_results:
            lines.append(f"- `{result.relative_file}`: {'; '.join(result.failure_reasons)}")
    else:
        lines.append("- None")

    lines.extend(["", "## OCR Failure Cases", ""])
    if ocr_failures:
        for result in ocr_failures:
            lines.append(f"- `{result.relative_file}`: {result.ocr.error or 'OCR returned no text'}")
    else:
        lines.append("- None")

    lines.extend(["", "## Scanned/Noisy PDFs Parsed Without OCR Fallback", ""])
    if scanned_without_ocr:
        for result in scanned_without_ocr:
            lines.append(f"- `{result.relative_file}`: pypdf extracted {result.text_char_count} characters")
    else:
        lines.append("- None")

    lines.extend(["", "## False Escalation Cases", ""])
    if false_escalations:
        for result in false_escalations:
            lines.append(f"- `{result.relative_file}`: actual escalations={_count(result.actual, 'escalation_items')}")
    else:
        lines.append("- None")

    lines.extend(["", "## RAID Extraction Misses", ""])
    if raid_misses:
        for result in raid_misses:
            lines.append(
                f"- `{result.relative_file}`: expected >= {result.expected.get('raid_items_min')}, "
                f"actual {_count(result.actual, 'raid_items')}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Classification Confusion Summary", ""])
    if confusions["classification"]:
        for (expected, actual), count in confusions["classification"].most_common():
            lines.append(f"- expected `{expected}` -> actual `{actual}`: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Governance Confusion Summary", ""])
    if confusions["governance"]:
        for (expected, actual), count in confusions["governance"].most_common():
            lines.append(f"- expected `{expected}` -> actual `{actual}`: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Extraction Summaries", ""])
    for result in results:
        lines.append(
            f"- `{result.relative_file}`: pass={result.passed}, "
            f"type={result.actual.get('document_type')}, relevance={result.actual.get('governance_relevance')}, "
            f"RAID={_count(result.actual, 'raid_items')}, escalations={_count(result.actual, 'escalation_items')}, "
            f"meeting_actions={_count(result.actual, 'meeting_actions')}, "
            f"OCR={result.ocr.fallback_triggered}, time={result.processing_time_seconds:.2f}s"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def run_regression_suite(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    markdown_report: Path = DEFAULT_MARKDOWN_REPORT,
    csv_report: Path = DEFAULT_CSV_REPORT,
) -> Dict[str, Any]:
    documents = discover_documents(corpus_dir)
    results = []
    for index, document in enumerate(documents, start=1):
        results.append(await process_document(document, index, len(documents)))

    metrics = compute_metrics(results)
    write_csv(results, csv_report)
    write_markdown(results, metrics, markdown_report)
    return {"results": results, "metrics": metrics}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run enterprise governance regression tests.")
    parser.add_argument("--corpus-dir", default=str(DEFAULT_CORPUS_DIR), help="Corpus root directory")
    parser.add_argument("--markdown-report", default=str(DEFAULT_MARKDOWN_REPORT), help="Markdown report path")
    parser.add_argument("--csv-report", default=str(DEFAULT_CSV_REPORT), help="CSV report path")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit non-zero when any document fails")
    args = parser.parse_args()

    result = asyncio.run(
        run_regression_suite(
            corpus_dir=Path(args.corpus_dir),
            markdown_report=Path(args.markdown_report),
            csv_report=Path(args.csv_report),
        )
    )
    metrics = result["metrics"]
    print("Regression suite complete.")
    print(f"Total files: {metrics['total']}")
    print(f"Passed: {metrics['passed']}")
    print(f"Failed: {metrics['failed']}")
    print(f"Pass %: {metrics['pass_percent']:.2f}%")
    print(f"Markdown report: {args.markdown_report}")
    print(f"CSV report: {args.csv_report}")
    return 1 if args.fail_on_regression and metrics["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
