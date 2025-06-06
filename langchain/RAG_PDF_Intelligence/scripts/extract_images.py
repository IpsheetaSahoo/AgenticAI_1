# scripts/extract_images.py
import fitz
from PIL import Image
import pytesseract
import io
from models import PDFChunk

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_ocr_chunks(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image = Image.open(io.BytesIO(base_image["image"]))
            text = pytesseract.image_to_string(image)

            if text.strip():
                validated = PDFChunk(page=page_num + 1, type='image', content=text.strip())
                chunks.append(validated)

    return chunks


