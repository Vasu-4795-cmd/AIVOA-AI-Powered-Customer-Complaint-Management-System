"""
Text extraction from uploaded complaint PDFs/emails.
Per the assignment brief, production-grade OCR is not required -- this
uses pypdf for text-layer extraction, which is sufficient for the
"realistic pharmaceutical complaint PDFs" demo files.
"""
import io
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if lower.endswith((".txt", ".eml")):
        return file_bytes.decode("utf-8", errors="ignore")
    # Fallback: try decoding as text
    return file_bytes.decode("utf-8", errors="ignore")
