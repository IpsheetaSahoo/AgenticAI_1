# scripts/extract_text.py
import fitz
from models import PDFChunk

def extract_text_chunks(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if text.strip():
            validated = PDFChunk(page=page_num + 1, type='text', content=text.strip())
            chunks.append(validated)

    return chunks


