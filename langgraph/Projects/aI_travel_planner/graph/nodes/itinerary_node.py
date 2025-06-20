# graph/nodes/itinerary_node.py

from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from tools.itinerary import generate_itinerary
from utils.schemas import TravelPlannerState


def create_itinerary_node():
    """
    Returns a Runnable node that calls the itinerary generation tool and updates the state.
    """
    def itinerary_node(state: TravelPlannerState) -> dict:
        user_input = state.user_input

        print("weather_data:", state.weather_data)
        print("hotel_data:", state.hotels_data)
        print("attraction_data:", state.attractions_data)
        print("start_date:", user_input.start_date)
        print("end_date:", user_input.end_date)
        print("budget_range:", user_input.budget_range)
        print("native_currency:", user_input.native_currency)

        result = generate_itinerary.invoke({
            "weather_data": state.weather_data,
            "hotels_data": state.hotels_data,
            "attractions_data": state.attractions_data,
            "start_date": str(user_input.start_date),
            "end_date": str(user_input.end_date),
            "budget_range": user_input.budget_range.model_dump(),
            "native_currency": user_input.native_currency
        })
        print("Itinerary generation result:", result)
        if "error" in result:
            print("[ERROR] Itinerary generation failed:", result["error"])
            return {"itinerary_data": None}
        return {"itinerary_data": result}

    return RunnableLambda(itinerary_node)
