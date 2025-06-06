from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any


def generate_embeddings(
    chunks: List[Dict[str, Any]],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[Dict[str, Any]]:
    """
    Use LangChain's HuggingFaceEmbeddings to embed semantic chunks.

    Returns:
        List of dicts with 'embedding', 'content', and 'metadata'
    """
    embedder = HuggingFaceEmbeddings(model_name=model_name)

    texts = [chunk["content"] for chunk in chunks]
    vectors = embedder.embed_documents(texts)

    embedded_chunks = []
    for i, chunk in enumerate(chunks):
        embedded_chunks.append({
            "embedding": vectors[i],
            "content": chunk["content"],
            "metadata": chunk["metadata"]
        })

    return embedded_chunks


# Optional test
if __name__ == "__main__":
    from semantic_chunker import semantic_chunking
    import os

    path = os.path.abspath("../data/business_report.pdf")
    semantic_chunks = semantic_chunking(path)

    result = generate_embeddings(semantic_chunks)
    print(f"✅ Embedded {len(result)} chunks.")
    print("Sample vector:", result[0]["embedding"][:5])
    print("Sample metadata:", result[0]["metadata"])
