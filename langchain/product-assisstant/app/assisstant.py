import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings

# Load environment variables
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')

# Define the Pydantic response model
class ProductInfo(BaseModel):
    product_name: str
    product_details: str
    price_usd: int

# Load simple product dict
def load_simple_product_db():
    path = Path(__file__).parent / "products.json"
    with open(path, "r") as f:
        return json.load(f)

# Create or load vector DB
def load_or_create_vector_db():
    persist_path = "app/chroma_store"
    embeddings = OpenAIEmbeddings()

    if os.path.exists(persist_path) and os.listdir(persist_path):
        # If persistence exists, load from disk
        vectordb = Chroma(persist_directory=persist_path, embedding_function=embeddings)
    else:
        # Else, create from scratch and persist
        loader = JSONLoader(file_path="products_complex.json", jq_schema=".", text_content=False)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        split_docs = text_splitter.split_documents(documents)

        vectordb = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            collection_name="products_collection",
            persist_directory=persist_path
        )

    return vectordb

# Initialize vector DB and simple DB at startup
simple_db = load_simple_product_db()
vectordb = load_or_create_vector_db()

# Initialize the LLM 
llm = ChatOpenAI(model="gpt-4o-mini")

# Set up the parser
parser = JsonOutputParser(pydantic_object=ProductInfo)

# Prompt template for semantic search summarization
prompt_template = PromptTemplate(
    input_variables=["context", "query"],
    template="""
You are a helpful assistant. Based on the following product info excerpts, answer the user query:

{context}

User query: {query}

Provide:
- product_name
- product_details
- price_usd

Answer in JSON format.
"""
)

# Function to get product info
def get_product_info(product_query: str) -> ProductInfo:
    # 1. Try exact match on simple DB
    for product_name in simple_db.keys():
        if product_query.lower() == product_name.lower():
            return ProductInfo(**simple_db[product_name])

    # 2. Semantic search from vector DB
    retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    relevant_docs = retriever.get_relevant_documents(product_query)

    if relevant_docs:
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        chain = prompt_template | llm
        llm_response = chain.invoke({"context": context, "query": product_query})

        try:
            parsed = json.loads(llm_response)
            return ProductInfo(**parsed)
        except Exception as e:
            print("Parsing LLM response failed:", e)

    # 3. Final fallback: LLM generation
    chat_prompt = ChatPromptTemplate.from_template(
        """You are a helpful assistant that provides structured product information in JSON format.

{format_instructions}

Please analyze the given product query and return:
- product_name
- product_details
- price_usd

Now, respond to the following product:

Product: {product}
"""
    ).partial(format_instructions=parser.get_format_instructions())

    chain = chat_prompt | llm | parser
    result_dict = chain.invoke({"product": product_query})
    return ProductInfo(**result_dict)
