"""
Document processing service: file validation, safe storage, and text extraction.
"""

import os
import uuid
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from config.settings import (
    UPLOADS_DIR,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
)

# Optional PyMuPDF (fitz) or pypdf
try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except ImportError:
    HAVE_PYMUPDF = False

try:
    from pypdf import PdfReader
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False


def validate_file_security(
    filename: str, file_bytes: bytes, is_photo: bool = False
) -> Tuple[bool, Optional[str]]:
    """Check file extension, file size, and basic byte header integrity."""
    ext = Path(filename).suffix.lower()
    allowed_exts = ALLOWED_IMAGE_EXTENSIONS if is_photo else ALLOWED_DOCUMENT_EXTENSIONS

    if ext not in allowed_exts:
        return False, f"File format '{ext}' is not permitted. Allowed: {', '.join(allowed_exts)}"

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds the permitted limit of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."

    if len(file_bytes) < 32:
        return False, "File is empty or corrupted (less than 32 bytes)."

    # Header check
    if ext == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            return False, "Invalid PDF header: file appears damaged or modified."
    elif ext in [".png", ".jpg", ".jpeg"]:
        try:
            import io
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception as e:
            return False, f"Invalid or corrupted image format: {e}"

    return True, None


def save_uploaded_file(
    application_id: str,
    doc_category: str,
    filename: str,
    file_bytes: bytes
) -> Tuple[str, str]:
    """Securely save uploaded file into structured directory with a sanitized unique name."""
    safe_app_dir = UPLOADS_DIR / application_id
    safe_app_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix.lower()
    safe_filename = f"{doc_category}_{uuid.uuid4().hex[:8]}{ext}"
    target_path = safe_app_dir / safe_filename

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return str(target_path), safe_filename


def extract_text_from_pdf(file_path: str) -> str:
    """Extract readable text from a PDF using PyMuPDF with pypdf fallback."""
    extracted_text = []

    if HAVE_PYMUPDF:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text = page.get_text()
                if text:
                    extracted_text.append(text)
            doc.close()
            if extracted_text:
                return "\n".join(extracted_text)
        except Exception:
            pass

    if HAVE_PYPDF:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            return "\n".join(extracted_text)
        except Exception:
            pass

    return ""


def extract_document_entities(text: str) -> Dict[str, Any]:
    """Parse text for common synthetic entities: PAN/National ID, Monthly Salary, Names, Dates."""
    entities: Dict[str, Any] = {}

    # PAN pattern (Standard 5 letters, 4 digits, 1 letter)
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    if pan_match:
        entities["detected_national_id"] = pan_match.group(0)

    # Passport pattern (1 letter + 7 digits)
    passport_match = re.search(r"\b[A-PR-WYa-pr-wy][1-9]\d{6}\b", text)
    if passport_match:
        entities["detected_passport"] = passport_match.group(0)

    # Income / Salary patterns
    salary_match = re.search(r"(?:Net\s+Salary|Net\s+Pay|Monthly\s+Income|Credit)[:\s]+(?:INR|Rs\.?|\$)?\s*([0-9,]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
    if salary_match:
        try:
            val = float(salary_match.group(1).replace(",", ""))
            entities["detected_monthly_income"] = val
        except ValueError:
            pass

    # Name pattern
    name_match = re.search(r"(?:Employee\s+Name|Name|Account\s+Holder)[:\s]+([A-Za-z\s]{3,35})", text, re.IGNORECASE)
    if name_match:
        entities["detected_name"] = name_match.group(1).strip()

    return entities
