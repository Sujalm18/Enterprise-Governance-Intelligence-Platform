# Project Summary

Enterprise Governance Intelligence Platform is an AI engineering portfolio project that turns mixed-format governance documents into structured governance intelligence.

## What It Does

- Ingests PDF, scanned PDF, DOCX, TXT, and XLSX documents.
- Classifies governance document type and relevance.
- Reconstructs ontology-aware governance entities.
- Extracts RAID items, meeting actions, and escalations with confidence scores.
- Suppresses false positives from generic policy and business documents.
- Provides a React review UI (Vite + TypeScript) and FastAPI backend.
- Runs an enterprise-style regression corpus.

## Engineering Highlights

- OCR-ready ingestion with quality-gated fallback.
- Stateful section-aware parsing.
- Governance ontology instead of flat keyword extraction.
- Semantic deduplication and conservative action validation.
- SQLite persistence with schema migration safeguards.
- Docker deployment artifacts and cloud deployment guidance.

## Why It Matters

The project demonstrates practical enterprise AI engineering: not just calling an LLM, but building the surrounding product architecture needed for trustworthy document intelligence.

