"""Lightweight, non-production document parsing (per assignment: production
grade OCR/parsing is not required). Supports .pdf, .txt/.eml (email text),
and images (best-effort OCR via pytesseract if available)."""
import io
from pypdf import PdfReader


def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text).strip()


def parse_text_or_email(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()


def parse_image(file_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img).strip()
    except Exception:
        # OCR engine not installed in this environment - not required by the
        # assignment. Caller falls back to letting the user paste/edit text.
        return ""


def extract_text(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    if lower.endswith((".txt", ".eml", ".msg")):
        return parse_text_or_email(file_bytes)
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return parse_image(file_bytes)
    # default: try decoding as text
    return parse_text_or_email(file_bytes)
