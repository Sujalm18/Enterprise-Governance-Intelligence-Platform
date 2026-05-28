import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from backend.app.services.ingestion.parser import parse_pdf, parse_pdf_ocr, MAX_OCR_PAGES

@patch("backend.app.services.ingestion.parser.PdfReader")
def test_searchable_pdf_bypasses_ocr(mock_pdf_reader):
    """
    Verifies that a standard searchable PDF containing 50+ characters
    is parsed normally via standard extraction and completely bypasses OCR fallback.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is a valid searchable PDF report containing more than fifty characters of text content."
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader
    
    # Mock parse_pdf_ocr to verify it is NEVER called
    with patch("backend.app.services.ingestion.parser.parse_pdf_ocr") as mock_ocr:
        res = parse_pdf(Path("dummy.pdf"))
        
        mock_ocr.assert_not_called()
        assert "searchable PDF" in res
        assert len(res) >= 50

@patch("backend.app.services.ingestion.parser.PdfReader")
@patch("backend.app.services.ingestion.parser.parse_pdf_ocr")
def test_scanned_pdf_triggers_ocr_fallback(mock_ocr, mock_pdf_reader):
    """
    Verifies that a scanned PDF returning less than 50 characters (e.g., empty or metadata-only)
    triggers the OCR fallback parser.
    """
    mock_page = MagicMock()
    # Returns fewer than 50 characters (triggers threshold fallback)
    mock_page.extract_text.return_value = "Short text." 
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader
    
    mock_ocr.return_value = "Parsed OCR text content output successfully."
    
    res = parse_pdf(Path("scanned.pdf"))
    
    # Verify that parse_pdf_ocr is invoked
    mock_ocr.assert_called_once_with(Path("scanned.pdf"))
    assert res == "Parsed OCR text content output successfully."

@patch("backend.app.services.ingestion.parser.fitz.open")
def test_ocr_exceeds_page_limit_guardrail(mock_fitz_open):
    """
    Verifies that a scanned PDF exceeding the MAX_OCR_PAGES (50 pages) limit
    raises a meaningful ValueError immediately.
    """
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = MAX_OCR_PAGES + 5  # 55 pages
    mock_fitz_open.return_value = mock_doc
    
    with pytest.raises(ValueError) as exc:
        parse_pdf_ocr(Path("huge_scan.pdf"))
        
    assert "exceeds safe guardrail limit" in str(exc.value)

@patch("backend.app.services.ingestion.parser.fitz.open")
@patch("backend.app.services.ingestion.parser._get_ocr_reader")
def test_ocr_metrics_and_text_assembly(mock_get_reader, mock_fitz_open):
    """
    Verifies that OCR fallback processes pages, retrieves confidence metrics,
    emits the standard metrics logging, and correctly aggregates page texts.
    """
    import numpy as np
    
    # 1. Mock Fitz Document & Page rendering with realistic pixmap attributes
    mock_pix_1 = MagicMock()
    mock_pix_1.samples = np.zeros((100, 200, 3), dtype=np.uint8).tobytes()
    mock_pix_1.height = 100
    mock_pix_1.width = 200
    mock_pix_1.n = 3
    
    mock_page_1 = MagicMock()
    mock_page_1.get_pixmap.return_value = mock_pix_1
    
    mock_pix_2 = MagicMock()
    mock_pix_2.samples = np.zeros((100, 200, 3), dtype=np.uint8).tobytes()
    mock_pix_2.height = 100
    mock_pix_2.width = 200
    mock_pix_2.n = 3
    
    mock_page_2 = MagicMock()
    mock_page_2.get_pixmap.return_value = mock_pix_2
    
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_doc.load_page.side_effect = [mock_page_1, mock_page_2]
    mock_fitz_open.return_value = mock_doc
    
    # 2. Mock EasyOCR Reader return values: [([bbox], text, confidence)]
    mock_reader = MagicMock()
    mock_reader.readtext.side_effect = [
        [([0, 0], "Governance", 0.95), ([1, 1], "Report", 0.85)],
        [([2, 2], "Milestones", 0.90)]
    ]
    mock_get_reader.return_value = mock_reader
    
    # 3. Call parse_pdf_ocr and verify outcomes
    res = parse_pdf_ocr(Path("scanned_report.pdf"))
    
    # Verify text is correctly aggregated
    assert "Governance Report" in res
    assert "Milestones" in res
    # Verify double newline separation per page
    assert res == "Governance Report\n\nMilestones"
    
    # Verify reader readtext was called twice (once per page)
    assert mock_reader.readtext.call_count == 2
    for call in mock_reader.readtext.call_args_list:
        img_arg = call.args[0]
        assert isinstance(img_arg, np.ndarray)
        assert img_arg.flags["C_CONTIGUOUS"]
        assert img_arg.dtype == np.uint8
