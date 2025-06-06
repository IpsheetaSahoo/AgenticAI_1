import time
from opensearch_connector import client
from embedder import generate_embeddings
from semantic_chunker import semantic_chunking
import os
import numpy as np
from typing import Dict, List

# ---------- CONFIG ----------
TOP_K = 5
SIMILARITY_METRIC = "cosine"  # or 'l2'
INDEX_NAMES = ["pdf_flat_index", "pdf_hnsw_index", "pdf_ivf_index"]
EMBEDDING_DIM = 384

# Store results here to be reused
performance_results: Dict[str, Dict] = {}


def evaluate_retrieval(query_embedding: List[float]) -> Dict[str, Dict]:
    """
    Evaluate top-K retrieval performance for each index.
    Returns a dictionary with average score, time, and top scores.
    """
    global performance_results
    performance_results = {}

    for index_name in INDEX_NAMES:
        start_time = time.time()
        response = client.search(
            index=index_name,
            body={
                "size": 1000,
                "_source": ["text", "embedding", "page_number", "chunk_id"],
                "query": {"match_all": {}}
            }
        )
        hits = response["hits"]["hits"]

        scores = []
        for hit in hits:
            doc_vec = np.array(hit["_source"]["embedding"])

            if SIMILARITY_METRIC == "cosine":
                score = np.dot(query_embedding, doc_vec) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_vec)
                )
            elif SIMILARITY_METRIC == "l2":
                score = -np.linalg.norm(query_embedding - doc_vec)
            else:
                score = 0

            scores.append(score)

        top_scores = sorted(scores, reverse=True)[:TOP_K]
        avg_score = np.mean(top_scores)
        end_time = time.time()

        performance_results[index_name] = {
            "average_top_k_score": round(avg_score, 4),
            "retrieval_time_sec": round(end_time - start_time, 4),
            "top_k_scores": [round(s, 4) for s in top_scores]
        }

    return performance_results


def get_best_index(metric: str = "hybrid") -> str:
    """
    Returns the best performing index based on:
    - 'score': highest average score
    - 'time': fastest retrieval time
    - 'hybrid': highest score first, then lower time as tie-breaker
    """
    if not performance_results:
        raise ValueError("⚠️ No performance results found. Please run evaluate_retrieval() first.")

    if metric == "score":
        return max(performance_results, key=lambda k: performance_results[k]["average_top_k_score"])

    elif metric == "time":
        return min(performance_results, key=lambda k: performance_results[k]["retrieval_time_sec"])

    elif metric == "hybrid":
        sorted_indexes = sorted(
            performance_results.items(),
            key=lambda x: (-x[1]["average_top_k_score"], x[1]["retrieval_time_sec"])
        )
        return sorted_indexes[0][0]

    else:
        raise ValueError("❌ Invalid metric. Choose from 'score', 'time', or 'hybrid'.")


# ---------- TEST ----------
if __name__ == "__main__":
    print("📊 Running Metrics Evaluation...")

    pdf_path = os.path.abspath("../data/business_report.pdf")
    chunks = semantic_chunking(pdf_path)
    query_embed = generate_embeddings([chunks[0]])[0]["embedding"]

    results = evaluate_retrieval(query_embed)

    print("\n📈 Performance Summary:")
    sorted_by_score_time = sorted(
        results.items(),
        key=lambda x: (-x[1]["average_top_k_score"], x[1]["retrieval_time_sec"])
    )

    for idx, (index_name, metrics) in enumerate(sorted_by_score_time, 1):
        print(f"\n{idx}. 📌 Index: {index_name}")
        print(f"   - 🔼 Avg Top-{TOP_K} Score: {metrics['average_top_k_score']}")
        print(f"   - ⏱️  Retrieval Time: {metrics['retrieval_time_sec']}s")
        print(f"   - 📈 Top {TOP_K} Scores: {metrics['top_k_scores']}")

    best = get_best_index("hybrid")
    print(f"\n✅ Best performing index (hybrid): {best}")
