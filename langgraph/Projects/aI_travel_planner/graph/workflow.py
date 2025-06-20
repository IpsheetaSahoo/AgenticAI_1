# graph/workflow.py

from langgraph.graph import StateGraph, END
from utils.schemas import TravelPlannerState
from graph.nodes.search_attractions_node import create_search_attractions_node
from graph.nodes.weather_node import create_weather_node
from graph.nodes.search_hotels_node import create_search_hotels_node
from graph.nodes.itinerary_node import create_itinerary_node
from graph.nodes.start_router_node import create_start_router_node

# 🔁 Map intent to node name
INTENT_TO_NODE = {
    "weather": "fetch_weather",
    "hotels": "fetch_hotels",
    "attractions": "search_attractions",
    "itinerary": "search_attractions"  # itinerary flow starts from attractions
}



def build_travel_planner_graph():
    """
    Constructs a dynamic LangGraph workflow with a start node that routes
    based on user query (weather, hotels, itinerary, etc.)
    """
    builder = StateGraph(TravelPlannerState)

    # ➕ Add Nodes
    builder.add_node("start_router", create_start_router_node())
    builder.add_node("search_attractions", create_search_attractions_node())
    builder.add_node("fetch_weather", create_weather_node())
    builder.add_node("fetch_hotels", create_search_hotels_node())
    builder.add_node("generate_itinerary", create_itinerary_node())

    # 🧭 Set Entry Point
    builder.set_entry_point("start_router")

    # 🔀 Conditional Routing from start_router → next node
    builder.add_conditional_edges(
        "start_router",
        lambda state: INTENT_TO_NODE.get(
            getattr(state.user_input, "query_intent", ""),  # fallback if missing
            "search_attractions"  # default fallback
        )
    )

    # ➡ Define static edges for itinerary flow
    builder.add_edge("search_attractions", "fetch_weather")
    builder.add_edge("fetch_weather", "fetch_hotels")
    builder.add_edge("fetch_hotels", "generate_itinerary")
    builder.add_edge("generate_itinerary", END)

    # For standalone tools
    builder.add_edge("fetch_weather", END)
    builder.add_edge("fetch_hotels", END)
    builder.add_edge("search_attractions", END)

    return builder.compile()
