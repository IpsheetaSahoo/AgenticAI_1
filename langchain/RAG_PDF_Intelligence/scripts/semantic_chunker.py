# scripts/semantic_chunker.py

import os
import uuid
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from models import PDFChunk
from extract_text import extract_text_chunks
from extract_tables import extract_table_chunks
from extract_images import extract_ocr_chunks

nltk.download("punkt", quiet=True)


def semantic_chunking(
    pdf_path: str,
    similarity_threshold: float = 0.7
) -> list[dict]:
    """
    Extracts and semantically chunks PDF content with metadata.
    Returns: List of dictionaries containing 'content' and 'metadata'.
    """

    filename = os.path.basename(pdf_path)

    # Step 1: Extract chunks
    text_chunks = extract_text_chunks(pdf_path)
    table_chunks = extract_table_chunks(pdf_path)
    image_chunks = extract_ocr_chunks(pdf_path)
    all_chunks: list[PDFChunk] = text_chunks + table_chunks + image_chunks

    # Step 2: Tokenize into sentences + track metadata
    sentence_blocks = []
    for chunk in all_chunks:
        for sent in sent_tokenize(chunk.content):
            if sent.strip():
                sentence_blocks.append({
                    "page": chunk.page,
                    "type": chunk.type,
                    "sentence": sent.strip(),
                })

    if not sentence_blocks:
        return []

    sentences = [item["sentence"] for item in sentence_blocks]
    sentence_meta = [{"page": item["page"], "type": item["type"]} for item in sentence_blocks]

    # Step 3: Embed sentences
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences)

    # Step 4: Semantic grouping
    semantic_chunks = []
    buffer = [sentences[0]]
    meta_buffer = [sentence_meta[0]]

    for i in range(1, len(sentences)):
        sim = cosine_similarity([embeddings[i - 1]], [embeddings[i]])[0][0]

        if sim > similarity_threshold:
            buffer.append(sentences[i])
            meta_buffer.append(sentence_meta[i])
        else:
            merged = " ".join(buffer)
            first_meta = meta_buffer[0]
            chunk_id = f"{first_meta['type']}_{first_meta['page']}_{uuid.uuid4().hex[:6]}"
            semantic_chunks.append({
                "content": merged,
                "metadata": {
                    "page": first_meta["page"],
                    "type": first_meta["type"],
                    "chunk_id": chunk_id,
                    "source": filename
                }
            })
            buffer = [sentences[i]]
            meta_buffer = [sentence_meta[i]]

    # Final flush
    if buffer:
        merged = " ".join(buffer)
        first_meta = meta_buffer[0]
        chunk_id = f"{first_meta['type']}_{first_meta['page']}_{uuid.uuid4().hex[:6]}"
        semantic_chunks.append({
            "content": merged,
            "metadata": {
                "page": first_meta["page"],
                "type": first_meta["type"],
                "chunk_id": chunk_id,
                "source": filename
            }
        })

    return semantic_chunks


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    pdf_path = os.path.abspath(
        os.path.join(base_dir, "../data/business_report.pdf")
    )
    chunks = semantic_chunking(pdf_path, similarity_threshold=0.7)

    print(f"Generated {len(chunks)} semantic chunks.\n")
    for idx, chunk in enumerate(chunks[:5]):
        print(f"--- Chunk {idx+1} ---\n{chunk['content']}\n[Meta] {chunk['metadata']}\n")
