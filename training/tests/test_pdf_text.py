import io
import sys
import unittest
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"lightweight_cv"))
from pdf_text import extract_pdf

def pdf_bytes(text=None, password=None):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    if text:
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(("BT /F1 12 Tf 10 700 Td ("+text+") Tj ET").encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    if password: writer.encrypt(password)
    output = io.BytesIO(); writer.write(output)
    return output.getvalue()

class PDFTests(unittest.TestCase):
    def test_real_text_is_preserved(self):
        self.assertIn("Paid work: used Python", extract_pdf(pdf_bytes("Paid work: used Python to parse logs.")))
    def test_blank_image_only_pdf_does_not_invent_text(self):
        with self.assertRaises(ValueError): extract_pdf(pdf_bytes())
    def test_invalid_large_and_encrypted_pdf_are_rejected(self):
        for data in [b"not pdf", b"%PDF-"+b"x"*(5*1024*1024), pdf_bytes("secret", "locked")]:
            with self.assertRaises(ValueError): extract_pdf(data)

if __name__ == "__main__": unittest.main()
