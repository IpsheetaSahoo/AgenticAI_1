from opensearch_connector import client
from embedder import generate_embeddings
from semantic_chunker import semantic_chunking
from embedder import generate_embeddings
import numpy as np
import os

# ---------- CONFIG ----------
INDEX_NAME = "pdf_hnsw_index"
TOP_K = 8             # Number of documents to retrieve before reranking
RERANKED_K = 3        # Final top-N after MMR
EMBEDDING_DIM = 384
LAMBDA_PARAM = 0.6    # MMR diversity-relevance balance



def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# ---------- Step 1: Retrieve from OpenSearch ----------
def retrieve_from_hnsw(query_embedding):
    response = client.search(
        index=INDEX_NAME,
        body={
            "size": TOP_K,
            "_source": ["text", "embedding", "page_number", "chunk_id"],
            "query": {"match_all": {}}
        }
    )

    hits = response["hits"]["hits"]
    retrieved = []
    for hit in hits:
        source = hit["_source"]
        retrieved.append({
            "text": source["text"],
            "embedding": np.array(source["embedding"]),
            "metadata": {
                "page_number": source.get("page_number"),
                "chunk_id": source.get("chunk_id")
            }
        })
    return retrieved


# ---------- Step 2: MMR Reranking ----------
def mmr_rerank(query_embedding, documents, top_n=3, lambda_param=0.5):
    """
    Rerank retrieved documents using Maximal Marginal Relevance (MMR).
    """
    # Step 1: Generate embeddings for retrieved documents
    docs_for_embedding = [{"content": doc["text"], "metadata": {}} for doc in documents]
    embedded_docs = generate_embeddings(docs_for_embedding)

    for i, doc in enumerate(documents):
        doc["embedding"] = embedded_docs[i]["embedding"]

    doc_embeddings = np.array([doc["embedding"] for doc in documents])
    selected = []
    unselected = list(range(len(documents)))

    for _ in range(min(top_n, len(documents))):
        mmr_scores = []

        for i in unselected:
            sim_to_query = cosine_similarity(query_embedding, doc_embeddings[i])
            sim_to_selected = max([cosine_similarity(doc_embeddings[i], doc_embeddings[j]) for j in selected], default=0)
            mmr_score = lambda_param * sim_to_query - (1 - lambda_param) * sim_to_selected
            mmr_scores.append((i, mmr_score))

        best_idx = max(mmr_scores, key=lambda x: x[1])[0]
        selected.append(best_idx)
        unselected.remove(best_idx)

    return [documents[i] for i in selected]


# ---------- MAIN ----------
if __name__ == "__main__":
    print("🔍 Running Reranking with HNSW index...")

    # Simulate a user query from existing document
    pdf_path = os.path.abspath("../data/business_report.pdf")
    chunks = semantic_chunking(pdf_path)
    query_text = chunks[0]
    query_embedding = generate_embeddings([query_text])[0]["embedding"]

    # Step 1: Retrieve top-K from HNSW index
    initial_results = retrieve_from_hnsw(query_embedding)

    # Step 2: Apply MMR reranking
    reranked = mmr_rerank(
        query_embedding=query_embedding,
        documents=initial_results,
        lambda_param=LAMBDA_PARAM,
        top_n=RERANKED_K
    )

    # Step 3: Show Results
    print(f"\n🎯 Top {RERANKED_K} MMR-Reranked Chunks:")
    for i, doc in enumerate(reranked):
        print(f"\nResult #{i+1}")
        print(f"Page: {doc['metadata']['page_number']}, Chunk ID: {doc['metadata']['chunk_id']}")
        print(f"Text: {doc['text'][:300]}...")
