"""
One-time setup script for shrimp export database
"""
from neo4j_schema import Neo4jSchemaBuilder
from data_loader import ShrimpDataLoader
from langchain_chatbot1 import ShrimpExportChatbot

import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    CSV_PATH = os.getenv("CSV_PATH")
    
    print("\n" + "="*80)
    print("SHRIMP EXPORT DATABASE SETUP")
    print("="*80 + "\n")
    
    # Step 1: Create Schema
    print("Step 1/3: Creating database schema...")
    schema_builder = Neo4jSchemaBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        schema_builder.create_constraints()
        schema_builder.create_indexes()
        if schema_builder.verify_schema():
            print("✓ Schema created successfully!\n")
        else:
            print("✗ Schema creation failed!\n")
            return
    finally:
        schema_builder.close()
    
    # Step 2: Load Data
    print("Step 2/3: Loading data from CSV...")
    print(f"Reading file: {CSV_PATH}")
    loader = ShrimpDataLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        loader.load_complete_dataset(CSV_PATH)
        print("✓ Data loaded successfully!\n")
    except Exception as e:
        print(f"✗ Data loading failed: {e}\n")
        return
    finally:
        loader.close()
    
    # Step 3: Test Connection
    print("Step 3/3: Testing chatbot connection...")
    chatbot = ShrimpExportChatbot(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    
    if chatbot.validate_connection():
        print("✓ Chatbot ready!\n")
        
        # Get statistics
        schema_builder = Neo4jSchemaBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        schema_builder.get_database_stats()
        schema_builder.close()
        
        print("\n" + "="*80)
        print("SETUP COMPLETE!")
        print("="*80)
        print("\nYou can now run the chatbot:")
        print("  python langchain_chatbot.py")
        print("\nOr test with a sample query:")
        print("  python test_query.py")
        print("="*80 + "\n")
    else:
        print("✗ Chatbot connection failed!\n")

if __name__ == "__main__":
    main()