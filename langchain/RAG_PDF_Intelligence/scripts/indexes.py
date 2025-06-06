from opensearch_connector import client
import faiss
import numpy as np

DIM = 384

def create_flat_index():
    body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": DIM,
                },
                "text": {"type": "text"}
            }
        }
    }
    client.indices.create(index="pdf_flat_index", body=body)
    print("[✓] Flat index created.")

def create_hnsw_index():
    body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": DIM,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "cosinesimil",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "text": {"type": "text"}
            }
        }
    }
    client.indices.create(index="pdf_hnsw_index", body=body)
    print("[✓] HNSW index created.")

def create_faiss_ivf_index(embedding_matrix, nlist=100):
    quantizer = faiss.IndexFlatL2(DIM)
    index_ivf = faiss.IndexIVFFlat(quantizer, DIM, nlist, faiss.METRIC_L2)
    index_ivf.train(embedding_matrix)
    index_ivf.add(embedding_matrix)
    faiss.write_index(index_ivf, "ivf_index.faiss")
    print("[✓] IVF index trained and saved.")

if __name__ == "__main__":
    if not client.indices.exists("pdf_flat_index"):
        create_flat_index()

    if not client.indices.exists("pdf_hnsw_index"):
        create_hnsw_index()

    dummy_vectors = np.random.rand(1000, DIM).astype("float32")
    create_faiss_ivf_index(dummy_vectors)
