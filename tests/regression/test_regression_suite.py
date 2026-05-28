from pathlib import Path

import pytest

from scripts.regression.run_regression_tests import (
    DEFAULT_CORPUS_DIR,
    discover_documents,
    run_regression_suite,
)


def test_regression_corpus_is_available():
    documents = discover_documents(DEFAULT_CORPUS_DIR)
    assert documents, "Regression corpus is empty or missing."
    assert all(Path(document).with_suffix(".expected.json").exists() for document in documents)


@pytest.mark.asyncio
async def test_regression_suite_executes_and_generates_reports(tmp_path):
    markdown_report = tmp_path / "regression_test_report.md"
    csv_report = tmp_path / "regression_results.csv"

    result = await run_regression_suite(
        corpus_dir=DEFAULT_CORPUS_DIR,
        markdown_report=markdown_report,
        csv_report=csv_report,
    )

    assert result["metrics"]["total"] > 0
    assert result["metrics"]["total"] == len(result["results"])
    assert markdown_report.exists()
    assert csv_report.exists()
    assert "Enterprise Regression Test Report" in markdown_report.read_text(encoding="utf-8")
