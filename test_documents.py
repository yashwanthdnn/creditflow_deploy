"""
Document Handling and Extraction Tests.
Tests file format restrictions, size thresholds, safe directory naming, and text extraction.
"""

import io
from PIL import Image
from services.document_service import (
    validate_file_security,
    save_uploaded_file,
    extract_document_entities
)
from services.ocr_service import perform_ocr_on_image


def test_unsupported_file_extension_blocked():
    """Test 4: Dangerous or unsupported file formats (.exe, .sh) are blocked."""
    is_valid, msg = validate_file_security("malicious_script.exe", b"MZDummyPayloadBinaryCode")
    assert is_valid is False
    assert "not permitted" in msg

    is_valid_sh, msg_sh = validate_file_security("payload.sh", b"#!/bin/bash\nrm -rf /")
    assert is_valid_sh is False


def test_file_size_limit_enforced():
    """Test file exceeding maximum limit is rejected."""
    oversized_bytes = b"0" * (12 * 1024 * 1024)  # 12 MB (limit 10 MB)
    is_valid, msg = validate_file_security("big_statement.pdf", oversized_bytes)
    assert is_valid is False
    assert "exceeds" in msg


def test_valid_image_document_security():
    """Test valid PNG image passes security checks."""
    img = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    is_valid, err = validate_file_security("applicant_photo.png", png_bytes, is_photo=True)
    assert is_valid is True
    assert err is None


def test_entity_regex_extraction():
    """Test parsing PAN, Salary, and Name from synthetic text."""
    sample_text = """
    CENTRAL INLAND REVENUE
    Permanent Account Number: ABCDE9988F
    Employee Name: Vikram Aditya
    Net Salary: INR 75,000.00
    """
    entities = extract_document_entities(sample_text)
    assert entities.get("detected_national_id") == "ABCDE9988F"
    assert entities.get("detected_monthly_income") == 75000.0
    assert "Vikram" in entities.get("detected_name", "")


def test_ocr_fallback_on_synthetic_image():
    """Test OCR handler gracefully executes on image and returns metadata."""
    img = Image.new("RGB", (300, 150), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(buf.getvalue())
        tmp_path = f.name

    ocr_res = perform_ocr_on_image(tmp_path)
    assert "image_dimensions" in ocr_res
    assert ocr_res["confidence"] > 0
