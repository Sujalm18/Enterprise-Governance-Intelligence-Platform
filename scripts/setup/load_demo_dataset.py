from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "data" / "demo"
CORPUS_DIR = ROOT / "data" / "regression" / "corpus"
SOURCES = [
    CORPUS_DIR / "project_status_reports" / "project_status_report_03_red.pdf",
    CORPUS_DIR / "raid_registers" / "raid_register_03.xlsx",
    CORPUS_DIR / "governance_reports" / "steering_committee_report_05.pdf",
    CORPUS_DIR / "escalation_memos" / "escalation_memo_01.pdf",
    CORPUS_DIR / "meeting_minutes" / "meeting_minutes_09.docx",
    CORPUS_DIR / "generic_business_docs" / "hr_policy_02.pdf",
]


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source in SOURCES:
        target = DEMO_DIR / source.name
        shutil.copy2(source, target)
        manifest.append({
            "filename": target.name,
            "source": str(source.relative_to(ROOT)),
            "demo_use": "Upload through Streamlit Upload Center or API /api/upload",
        })
    (DEMO_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Demo dataset ready: {DEMO_DIR}")
    print(f"Files copied: {len(manifest)}")


if __name__ == "__main__":
    main()
