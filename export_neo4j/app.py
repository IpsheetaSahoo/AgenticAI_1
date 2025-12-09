"""
FastAPI Application for Shrimp Export Data Chatbot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import logging
from langchain_chatbot import ShrimpExportChatbot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Shrimp Export Analysis API",
    description="Natural language query interface for shrimp export data analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot = None


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Show me the top 5 exporters by FOB value"
            }
        }


class QueryResponse(BaseModel):
    question: str
    answer: str
    cypher_query: Optional[str] = None
    raw_data: Optional[List[Dict[str, Any]]] = None
    status: str = "success"


class HealthResponse(BaseModel):
    status: str
    neo4j_connected: bool
    message: str


class SchemaResponse(BaseModel):
    schema: str
    node_types: List[str]
    relationship_types: List[str]


@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    
    logger.info("Starting Shrimp Export Analysis API...")
    
    try:
        # Get configuration from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not neo4j_password:
            raise ValueError("NEO4J_PASSWORD not set in environment")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        # Initialize chatbot
        chatbot = ShrimpExportChatbot(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4")
        )
        
        # Validate connection
        if chatbot.validate_connection():
            logger.info("✓ Chatbot initialized successfully")
        else:
            raise Exception("Neo4j connection validation failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global chatbot
    if chatbot:
        chatbot.close()
        logger.info("Chatbot connection closed")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Shrimp Export Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global chatbot
    
    if chatbot is None:
        return HealthResponse(
            status="unhealthy",
            neo4j_connected=False,
            message="Chatbot not initialized"
        )
    
    try:
        is_connected = chatbot.validate_connection()
        return HealthResponse(
            status="healthy" if is_connected else "unhealthy",
            neo4j_connected=is_connected,
            message="All systems operational" if is_connected else "Neo4j connection failed"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            neo4j_connected=False,
            message=f"Health check failed: {str(e)}"
        )


@app.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """Get database schema information"""
    global chatbot
    
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        schema_info = chatbot.get_schema_info()
        
        # Parse schema for node and relationship types
        node_types = ["Shipment", "Product", "Exporter", "Consignee", 
                     "Country", "IndianPort", "DestinationPort", "TimeMonth"]
        relationship_types = ["SHIPPED", "CONTAINS", "SENT_TO", "EXPORTED_TO",
                            "DEPARTED_FROM", "ARRIVED_AT", "OCCURRED_IN", "LOCATED_IN"]
        
        return SchemaResponse(
            schema=schema_info,
            node_types=node_types,
            relationship_types=relationship_types
        )
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """
    Query the shrimp export database using natural language
    
    Example questions:
    - "Show me the top 5 exporters by FOB value"
    - "What were the December exports for the last 3 years?"
    - "Which countries import the most shrimp?"
    - "Show me export trends for 2023"
    """
    global chatbot
    
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Get answer from chatbot
        result = chatbot.ask(request.question)
        
        # Handle error cases
        if result.get("answer", "").startswith("Error:"):
            return QueryResponse(
                question=request.question,
                answer=result.get("answer", "An error occurred"),
                cypher_query=result.get("cypher_query"),
                raw_data=None,
                status="error"
            )
        
        return QueryResponse(
            question=request.question,
            answer=result.get("answer", "No answer generated"),
            cypher_query=result.get("cypher_query"),
            raw_data=result.get("raw_data", [])[:10],  # Limit to 10 results for API
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/examples")
async def get_example_queries():
    """Get example queries that users can try"""
    return {
        "examples": [
            {
                "category": "Temporal Analysis",
                "queries": [
                    "Show me December exports for the last 3 years",
                    "What were the monthly export trends in 2023?",
                    "Compare Q1 and Q2 performance in 2022"
                ]
            },
            {
                "category": "Exporter Analysis",
                "queries": [
                    "Who are the top 10 exporters by FOB value?",
                    "Which exporters have the most consistent pricing?",
                    "Show me exporters who ship to USA"
                ]
            },
            {
                "category": "Product Analysis",
                "queries": [
                    "What are the most common product specifications?",
                    "Which products have the highest unit prices?",
                    "Show me total quantity by product type"
                ]
            },
            {
                "category": "Market Analysis",
                "queries": [
                    "Which countries import the most shrimp?",
                    "What's the average unit price to USA?",
                    "Show me destination countries with highest FOB values"
                ]
            },
            {
                "category": "Route Analysis",
                "queries": [
                    "Which port pairs are most frequently used?",
                    "Show me all shipments from Chennai",
                    "What are the top destination ports?"
                ]
            }
        ]
    }


@app.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    global chatbot
    
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        # Query for node counts
        node_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """
        
        # Query for relationship counts
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship, count(r) as count
        ORDER BY count DESC
        """
        
        node_result = chatbot.graph.query(node_query)
        rel_result = chatbot.graph.query(rel_query)
        
        return {
            "nodes": {item["label"]: item["count"] for item in node_result},
            "relationships": {item["relationship"]: item["count"] for item in rel_result}
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )