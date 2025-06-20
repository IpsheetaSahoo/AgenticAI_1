"""
Node that calls the get_top_hotels LangChain tool
and updates the LangGraph state with the hotel data.
"""

from typing import Callable
from tools.hotels import get_top_hotels
from utils.schemas import TravelPlannerState


def create_search_hotels_node() -> Callable[[TravelPlannerState], TravelPlannerState]:
    """
    LangGraph node to call the hotel search tool using city name,
    and store the results in the LangGraph state.
    """
    def search_hotels(state: TravelPlannerState) -> TravelPlannerState:
        print(f"[NODE] Searching hotels for city: {state.user_input.destination_city}")

        # Call the LangChain tool with city as input
        tool_output = get_top_hotels.invoke({
            "city": state.user_input.destination_city
        })

        # Update and return new state with hotel data
        return state.model_copy(update={"hotels_data": tool_output})

    return search_hotels
