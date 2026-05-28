import os
import tempfile
import pytest
from backend.app.services.ingestion.cleaner import clean_text
from backend.app.services.ingestion.chunker import chunk_text
from backend.app.services.ingestion.parser import parse_file

def test_clean_text():
    raw_text = "Project Apollo  \r\n\r\n  has some \t control \x00 characters and extra   whitespace."
    cleaned = clean_text(raw_text)
    assert "  " not in cleaned  # Double spaces collapsed
    assert "\r" not in cleaned   # Line endings normalized
    assert "\x00" not in cleaned # Control characters removed
    assert cleaned.startswith("Project Apollo")

def test_chunk_text():
    text = "abcdefghijklmnopqrstuvwxyz" * 10  # 260 chars
    chunks = chunk_text(text, document_id=1, filename="test.txt", chunk_size=100, chunk_overlap=20)
    
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "chunk_index" in first_chunk
    assert first_chunk["metadata"]["document_id"] == 1
    assert first_chunk["metadata"]["filename"] == "test.txt"
    assert len(first_chunk["text"]) <= 100

def test_parse_text_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write("Enterprise Status Update: All milestones green.")
        temp_path = temp_file.name
        
    try:
        parsed_text = parse_file(temp_path, "txt")
        assert "All milestones green" in parsed_text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
