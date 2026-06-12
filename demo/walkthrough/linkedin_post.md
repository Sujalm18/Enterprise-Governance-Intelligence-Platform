# LinkedIn Post Draft

I built an Enterprise Governance Intelligence Platform as a portfolio project to explore a harder version of document AI: not just summarizing PDFs, but extracting trustworthy governance signals from messy enterprise documents.

The system processes PDFs, DOCX, TXT, XLSX, searchable PDFs, and OCR-ready scanned PDFs. It classifies documents such as project status reports, RAID registers, steering committee packs, escalation memos, meeting minutes, and generic business documents.

The most interesting engineering challenge was precision. A simple keyword pipeline will turn policy statements into actions, approvals into escalations, and every line of a RAID spreadsheet into a separate item. I implemented an ontology-aware extraction layer that reconstructs governance objects first, then maps only legitimate risks, issues, dependencies, escalations, and accountable actions into the user-facing outputs.

Highlights:

- FastAPI backend and React review UI
- OCR-ready ingestion pipeline
- Governance taxonomy and ontology-aware parsing
- Semantic deduplication and false-positive suppression
- SQLite persistence with migration safeguards
- 90-document regression framework
- Docker deployment artifacts and architecture docs

This project reinforced a lesson I keep coming back to: enterprise AI is less about a single model call and more about the system around it: data quality, workflow, validation, observability, and honest evaluation.

