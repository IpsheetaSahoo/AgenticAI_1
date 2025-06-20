"""
Tool to fetch top hotels using the Google Serper Tool via LangChain.
"""

from langchain_core.tools import tool
from langchain_community.tools.google_serper.tool import GoogleSerperAPIWrapper
from pydantic import BaseModel, Field
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables and set Serper API key
load_dotenv()
os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')

# Initialize Google Serper search wrapper
search = GoogleSerperAPIWrapper()

class HotelSearchInput(BaseModel):
    city: str = Field(..., description="City to search for hotels")

@tool(args_schema=HotelSearchInput)
def get_top_hotels(city: str) -> List[Dict]:
    """
    Uses Google Serper via LangChain to search for top hotels in a city.
    Returns a list of hotel names and their links.
    """
    print(f"[TOOL] Searching for hotels in {city} using Serper...")

    query = f"Best hotels in {city}"
    results = search.results(query)
    print("Structured results:", results)
    hotels = results.get("organic", [])[:5]  # Get top 5 organic results

    return [
        {
            "title": r.get("title"),
            "link": r.get("link")
        }
        for r in hotels if r.get("title") and r.get("link")
    ]
