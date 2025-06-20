from graph.workflow import build_travel_planner_graph
from utils.schemas import UserInput, TravelPlannerState
from dotenv import load_dotenv

load_dotenv()

def main():
    # 1. Collect user input
    user_input = UserInput(
        destination_city="Barcelona",
        start_date="2025-06-20",
        end_date="2025-06-25",
        budget_range={"min": 800, "max": 1500},
        native_currency="EUR"
    )

    # 2. Initialize LangGraph and invoke planner
    initial_state = TravelPlannerState(user_input=user_input)
    graph = build_travel_planner_graph()
    final_state = graph.invoke(initial_state)

    # 3. Show itinerary only
    print("\n🗺️ Travel Itinerary")
    itinerary = final_state.get("itinerary_data", {})
    if not itinerary:
        print("Itinerary generation failed.")
        return

    print("📌 Summary:", itinerary.get("summary", "N/A"))
    print(f"💰 Total Cost: {itinerary.get('total_cost')} {itinerary.get('currency')}")
    print("\n📅 Detailed Plan:")

    for day in itinerary.get("detailed_itinerary", []):
        print(f"{day.get('day')}, {day.get('date')}:")
        for activity in day.get("activities", []):
            icon = activity.get("icon", "")
            desc = activity.get("description", "")
            print(f"   {icon} {desc}")
        print(f"   🌤️ Weather: {day.get('weather', 'N/A')}")
        print(f"   📝 Notes: {day.get('notes', 'No notes')}\n")

if __name__ == "__main__":
    main()
