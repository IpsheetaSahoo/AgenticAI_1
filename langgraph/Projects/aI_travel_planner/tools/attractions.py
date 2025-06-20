"""
Tool to fetch top tourist attractions using the Google Serper Tool via LangChain.
"""

from langchain_core.tools import tool, Tool
from langchain_community.tools.google_serper.tool import GoogleSerperAPIWrapper
from pydantic import BaseModel, Field
from typing import List, Dict
import os
from dotenv import load_dotenv
import json

load_dotenv()
os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')

# Set up Google Serper tool manually
search = GoogleSerperAPIWrapper()


class AttractionInput(BaseModel):
    city: str = Field(..., description="City to search for attractions and restaurants")


@tool(args_schema=AttractionInput)
def get_top_attractions(city: str) -> List[Dict]:
    """
    Uses Google Serper via LangChain to search for top tourist attractions and nearby restaurants in a city.
    Returns a list of title + link.
    """
    print(f"[TOOL] Searching for attractions and nearby restaurants in {city} using Serper...")

    query = f"Top tourist attractions and restaurants in {city}"
    results = search.results(query)
    print("Structured results:", results)
    attractions = results.get("organic", [])[:2]
    print("Attractions list:", attractions)
    return [
        {
            "title": r.get("title"),
            "link": r.get("link")
        }
        for r in attractions if r.get("title") and r.get("link")
    ]
