"""
graph/nodes/search_attractions_node.py

This module defines a LangGraph-compatible node for retrieving attractions 
data based on user input. It wraps the `get_top_attractions` LangChain tool 
and updates the LangGraph state with the structured results.

The node retrieves city-level attractions and stores them in the graph state 
for downstream use in itinerary generation and cost calculation.

Exports:
- create_search_attractions_node: Returns a LangGraph-ready callable node function
"""
# graph/nodes/search_attractions_node.py

from langchain_core.runnables import Runnable
from graph.workflow import TravelPlannerState
from tools.attractions import get_top_attractions
from typing import Callable


def create_search_attractions_node() -> Callable[[TravelPlannerState], TravelPlannerState]:
    
    """
    Node that calls the get_top_attractions LangChain tool
    and updates the LangGraph state with the attractions data.
    """

    def search_attractions(state: TravelPlannerState) -> TravelPlannerState:
        print(f"[NODE] Searching attractions and restaurants for city: {state.user_input.destination_city}")

        # Call LangChain tool with destination city
        tool_output = get_top_attractions.invoke({
            "city": state.user_input.destination_city
        })

        # tool_output is a list of dicts with 'title' and 'link'
        # Update and return new state
        print("Tool output:", tool_output)
        return state.model_copy(update={"attractions_data": tool_output})

    return search_attractions
