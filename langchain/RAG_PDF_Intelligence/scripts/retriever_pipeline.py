from opensearch_connector import client
from typing import List, Dict
import numpy as np

# ---------- CONFIG ----------
INDEX_NAMES = ["pdf_flat_index", "pdf_hnsw_index", "pdf_ivf_index"]
TOP_K = 5
SIMILARITY_METRIC = "cosine"  # Change to 'l2' for Euclidean
EMBEDDING_DIM = 384  # depends on your embedding model

# ---------- HELPER FUNCTION ----------
def cosine_similarity_score(query_vec, doc_vec):
    """Compute cosine similarity between two vectors."""
    query_vec = np.array(query_vec)
    doc_vec = np.array(doc_vec)
    if np.linalg.norm(query_vec) == 0 or np.linalg.norm(doc_vec) == 0:
        return 0
    return np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))


def l2_distance_score(query_vec, doc_vec):
    """Compute negative Euclidean distance (closer = higher score)."""
    query_vec = np.array(query_vec)
    doc_vec = np.array(doc_vec)
    return -np.linalg.norm(query_vec - doc_vec)


# ---------- RETRIEVER FUNCTION ----------
def retrieve_top_k(query_embedding: List[float]) -> Dict[str, List[Dict]]:
    """
    Query all 3 indexes and return top K documents for each with score and metadata.
    """
    results = {}

    for index_name in INDEX_NAMES:
        response = client.search(
            index=index_name,
            body={
                "size": 1000,  # fetch all and filter later
                "_source": ["text", "embedding", "page_number", "chunk_id"],
                "query": {"match_all": {}}
            }
        )

        hits = response["hits"]["hits"]

        # Compute similarity
        scored_hits = []
        for hit in hits:
            source = hit["_source"]
            doc_vec = source["embedding"]

            if SIMILARITY_METRIC == "cosine":
                score = cosine_similarity_score(query_embedding, doc_vec)
            elif SIMILARITY_METRIC == "l2":
                score = l2_distance_score(query_embedding, doc_vec)
            else:
                raise ValueError("Unsupported similarity metric.")

            scored_hits.append({
                "text": source["text"],
                "metadata": {
                    "page_number": source.get("page_number"),
                    "chunk_id": source.get("chunk_id")
                },
                "score": score
            })

        # Sort and take top-K
        sorted_hits = sorted(scored_hits, key=lambda x: x["score"], reverse=True)[:TOP_K]
        results[index_name] = sorted_hits

    return results


# ---------- TEST ----------
if __name__ == "__main__":
    from embedder import generate_embeddings
    from semantic_chunker import semantic_chunking
    import os

    # Sample query from PDF
    pdf_path = os.path.abspath("../data/business_report.pdf")
    chunks = semantic_chunking(pdf_path)
    embedded = generate_embeddings([chunks[0]])  # Take only 1 sample chunk for testing

    print("🔍 Running retrieval...")
    top_docs = retrieve_top_k(embedded[0]["embedding"])

    for index_name, docs in top_docs.items():
        print(f"\n📌 Top docs from: {index_name}")
        for doc in docs:
            print(f"- [Score: {round(doc['score'], 4)}] Page: {doc['metadata']['page_number']} | Chunk: {doc['metadata']['chunk_id']}")
            print(f"  Text: {doc['text'][:100]}...\n")
