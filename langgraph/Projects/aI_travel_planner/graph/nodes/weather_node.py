# nodes/weather_node.py

"""
weather_node.py

LangGraph node for fetching weather forecast using the `get_weather_forecast` tool.
Updates the TravelPlannerState with weather data.
"""

from typing import Callable
from tools.weather import get_weather_forecast
from utils.schemas import TravelPlannerState


def create_weather_node() -> Callable[[TravelPlannerState], TravelPlannerState]:
    """
    Returns a LangGraph node that fetches the weather forecast
    and updates the graph state with the response.
    """

    def weather_node(state: TravelPlannerState) -> TravelPlannerState:
        print(f"[NODE] Fetching weather for: {state.user_input.destination_city} "
              f"from {state.user_input.start_date} to {state.user_input.end_date}")

        forecast_result = get_weather_forecast.invoke({
            "location": state.user_input.destination_city,
            "start_date": state.user_input.start_date.isoformat(),
            "end_date": state.user_input.end_date.isoformat()
        })

        # Check if error occurred
        if "error" in forecast_result:
            print("[ERROR] Weather fetch failed:", forecast_result["error"])
            return state  # return unchanged state

        # Update state with forecast data
        return state.model_copy(update={"weather_data": forecast_result})

    return weather_node
