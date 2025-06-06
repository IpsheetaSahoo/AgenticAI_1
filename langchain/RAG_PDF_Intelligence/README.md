# 🧠 RAG PDF Intelligence

A modular, production-ready pipeline that extracts insights from business PDFs using **Retrieval-Augmented Generation (RAG)** powered by **LLMs**, **semantic chunking**, and **OpenSearch** for vector search.

---

## 📈 Business Relevance

Modern businesses store vital information in **unstructured PDF documents** such as financial reports, audits, reviews, or contracts. This tool allows:
- Intelligent extraction of **text, tables, and images**
- **Context-aware retrieval** using embeddings and reranking
- Generative answering via LLMs (OpenAI GPT-4o-mini)
- Auto-saving of insights in a **professional DOCX report**

> 🔁 Ideal for automation, audit teams, analysts, and GenAI-powered business dashboards.

---

## 📂 Folder Structure

```bash
RAG_PDF_Intelligence/
├── data/                   # Sample input PDFs (like business_report.pdf)
│   └── business_report.pdf
├── outputs/                # LLM answers saved as DOCX
├── scripts/                # Modular scripts for pipeline components
├── requirements.txt        # Python dependencies
├── .gitignore              # Clean Git commits
└── README.md               # Project documentation

🛠️ Setup Instructions

1. Clone the Repo

git clone https://github.com/IpsheetaSahoo/AgenticAI_1.git
cd langchain
cd RAG_PDF_Intelligence

2. Create and Activate Virtual Environment

conda create -n rag_env python=3.10 -y
conda activate rag_env

3. Install Dependencies

pip install -r requirements.txt

4. Set OpenAI API Key
Create a .env file in the root with:

OPENAI_API_KEY=your_openai_key_here


🧪 How to Run a Test
We’ve included a sample document (data/business_report.pdf) for demonstration.

✅ Step-by-Step

cd scripts
python rag_engine.py

This will:
Extract data from the sample PDF
Generate semantic chunks
Embed into OpenSearch
Run the RAG pipeline
Save the final answer to: outputs/rag_response_output.docx

| Script                  | Description                  |
| ----------------------- | ---------------------------- |
| `extract_text.py`       | Extracts paragraphs from PDF |
| `extract_tables.py`     | Parses structured tables     |
| `extract_images.py`     | Captures embedded visuals    |
| `semantic_chunker.py`   | Chunking for embedding       |
| `embedder.py`           | HuggingFace embedding logic  |
| `insert_embeddings.py`  | Pushes to OpenSearch         |
| `retriever_pipeline.py` | Retrieves top-K vectors      |
| `reranking.py`          | Applies MMR reranking        |
| `rag_engine.py`         | End-to-end LLM generation    |


💼 Future Scope
RPA integration for automated PDF intake & output dispatch

Milvus/OpenSearch hybrid search

Streamlit UI for non-tech users

Metadata-based filtering

Re-ranking with BM25 + MMR


