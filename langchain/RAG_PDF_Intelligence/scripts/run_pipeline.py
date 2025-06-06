from semantic_chunker import semantic_chunking

#all_chunks is a list of PDFChunk from text, tables, images
semantic_chunks = semantic_chunking(all_chunks, similarity_threshold=0.7)

# Preview
print(semantic_chunks[0])
