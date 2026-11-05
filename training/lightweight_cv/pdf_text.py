"""Bounded PDF text extraction in an expendable worker; no OCR or model labels."""
import io
import sys
from pypdf import PdfReader

MAX_BYTES = 5 * 1024 * 1024

def extract_pdf(data):
    if not data.startswith(b"%PDF-") or len(data) > MAX_BYTES:
        raise ValueError("Invalid PDF or size limit")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 50:
        raise ValueError("Encrypted PDF or page limit")
    parts = []
    for page in reader.pages:
        contents = page.get_contents()
        if contents and len(contents.get_data()) > 10 * 1024 * 1024:
            raise ValueError("PDF content stream too large")
        parts.append(page.extract_text() or "")
        if sum(map(len, parts)) + len(parts) > 30000:
            raise ValueError("CV text exceeds 30000 characters")
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("PDF has no text layer; OCR is not enabled")
    return text

if __name__ == "__main__":
    try:
        text = extract_pdf(sys.stdin.buffer.read(MAX_BYTES + 1))
        sys.stdout.buffer.write(text.encode("utf-8"))
    except Exception:
        raise SystemExit(2)
