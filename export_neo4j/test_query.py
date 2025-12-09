"""
Test queries to verify installation
"""
from langchain_chatbot import ShrimpExportChatbot
import os
from dotenv import load_dotenv

load_dotenv()

def test_queries():
    # Initialize chatbot
    chatbot = ShrimpExportChatbot(
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("NEO4J_USER"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini"
    )
    
    # Test queries
    test_questions = [
        # "How many total shipments are in the database?",
        # "What are the top 5 exporters by value?",
        # "Which countries receive the most exports?",
        "Show me exports for December 2023"
    ]
    
    print("\n" + "="*80)
    print("RUNNING TEST QUERIES")
    print("="*80 + "\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}/4: {question}")
        print("-"*80)
        
        result = chatbot.ask(question)
        
        print(f"Generated Cypher:\n{result['cypher_query']}\n")
        print(f"Answer:\n{result['answer']}\n")
        print("="*80)

if __name__ == "__main__":
    test_queries()