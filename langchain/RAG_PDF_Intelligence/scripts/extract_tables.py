# scripts/extract_tables.py
import pdfplumber
from models import PDFChunk

def extract_table_chunks(pdf_path):
    chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table_index, table in enumerate(tables):
                if not table:
                    continue
                formatted = "\n".join([
                    "\t".join([cell if cell else "" for cell in row])
                    for row in table if any(row)
                ])
                if formatted.strip():
                    validated = PDFChunk(page=page_num + 1, type='table', content=formatted.strip())
                    chunks.append(validated)

    return chunks

