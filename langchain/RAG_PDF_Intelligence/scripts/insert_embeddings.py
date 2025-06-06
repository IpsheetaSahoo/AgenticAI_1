import os
import uuid
from opensearch_connector import client  # ✅ Reuse the existing connection
from embedder import generate_embeddings
from semantic_chunker import semantic_chunking

# Load and chunk the PDF
pdf_path = os.path.abspath("../data/business_report.pdf")
chunks = semantic_chunking(pdf_path)

# Generate embeddings
embedded_chunks = generate_embeddings(chunks)

# Index names
index_names = ["pdf_flat_index", "pdf_hnsw_index", "pdf_ivf_index"]

# Insert documents into each index
for chunk in embedded_chunks:
    doc = {
        "text": chunk["content"],
        "embedding": chunk["embedding"],
        **chunk["metadata"]  # page, etc.
    }

    for index_name in index_names:
        client.index(
            index=index_name,
            id=str(uuid.uuid4()),  # unique document ID
            body=doc
        )

print(f"✅ Inserted {len(embedded_chunks)} documents into each index.")

results = client.search(
    index="pdf_flat_index",
    body={"query": {"match_all": {}}, "size": 5}
)

for hit in results["hits"]["hits"]:
    print("\n📄 Document:")
    print("Text:", hit["_source"]["text"][:100], "...")
    print("Vector (first 5):", hit["_source"]["embedding"][:5])
    print("Page:", hit["_source"].get("page"))
