# app.py

import streamlit as st
from utils.schemas import UserInput, TravelPlannerState
from graph.workflow import build_travel_planner_graph
from datetime import date
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Travel Planner", layout="wide")
st.title("✈️ AI Travel Planner")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.chat_input("Ask your travel question or plan a trip...")

# --- Collect user input from Streamlit widgets ---
city = st.text_input("Destination city", "Barcelona")
start = st.date_input("Start date", date(2025, 6, 20))
end = st.date_input("End date", date(2025, 6, 25))
min_budget = st.number_input("Min budget", value=800)
max_budget = st.number_input("Max budget", value=1500)
currency = st.selectbox("Currency", ["EUR", "USD", "INR", "GBP", "JPY", "CAD", "AUD"], index=0)

if user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.markdown(user_query)

    user_input = UserInput(
        destination_city=city,
        start_date=start,
        end_date=end,
        budget_range={"min": min_budget, "max": max_budget},
        native_currency=currency,
        raw_query=user_query,
        query_intent=None  # Let start_router set this
    )

    initial_state = TravelPlannerState(user_input=user_input)
    graph = build_travel_planner_graph()
    final_state = graph.invoke(initial_state)

    with st.chat_message("assistant"):
        itinerary = final_state.get("itinerary_data", {})
        if itinerary:
            st.subheader("🗺️ Travel Itinerary")
            st.markdown(f"**📌 Summary:** {itinerary.get('summary', 'N/A')}")
            st.markdown(f"**💰 Total Cost:** {itinerary.get('total_cost')} {itinerary.get('currency')}")

            st.markdown("### 📅 Detailed Plan:")
            for day in itinerary.get("detailed_itinerary", []):
                st.markdown(f"**{day.get('day')}, {day.get('date')}**")
                for activity in day.get("activities", []):
                    icon = activity.get("icon", "")
                    desc = activity.get("description", "")
                    st.markdown(f"- {icon} {desc}")
                st.markdown(f"🌤️ **Weather:** {day.get('weather', 'N/A')}")
                st.markdown(f"📝 **Notes:** {day.get('notes', 'No notes')}")
                st.markdown("---")
        else:
            st.warning("⚠️ No itinerary found or request was not itinerary-related.")
