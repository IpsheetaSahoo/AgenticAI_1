# 🧳 AI Travel Planner (LangGraph + LangChain + Streamlit)

This project is an AI-powered **Travel Planning Assistant** that dynamically generates detailed, day-wise itineraries for your trips. Powered by **LangGraph**, **LangChain**, and **Streamlit**, the system uses 
tools like Google Serper and OpenWeatherMap to provide real-time information on **weather**, **hotels**, **attractions**, and **total travel cost**, customized to your budget and destination.

---

## 🚀 Features

- **Chat-like interface** with natural language query support (via Streamlit).
- **Intent classification** using LLM to route requests to relevant tools:
  - Weather-only queries
  - Hotel search
  - Attractions lookup
  - Full itinerary with cost estimation
- **Tool integration** with:
  - 🌐 Google Serper for attractions and hotels
  - ☁️ OpenWeatherMap (via Open-Meteo API)
  - 💸 Currency conversion via ExchangeRate.host
- **Dynamic LangGraph routing** based on user intent
- **Pydantic schemas** and LangChain-compatible tools for state management
- **LLM-based itinerary generation** using prompt chaining

---

## 🗂️ Project Structure

```text
├── app.py                    # Streamlit frontend with chat interface
├── main.py                   # CLI-style test runner for full itinerary
├── tools/
│   ├── attractions.py        # Serper tool to fetch attractions
│   ├── hotels.py             # Serper tool to fetch hotels
│   ├── weather.py            # Open-Meteo based forecast tool
│   └── itinerary.py          # Custom LLM chain to generate detailed trip plans
├── graph/
│   ├── workflow.py           # LangGraph workflow with routing
│   └── nodes/
│       ├── start_router_node.py      # LLM node to classify intent
│       ├── search_attractions_node.py
│       ├── weather_node.py
│       ├── search_hotels_node.py
│       └── itinerary_node.py
├── utils/
│   ├── schemas.py            # Pydantic models for state and user input
├── .env                      # Contains API keys
├── requirements.txt          # Dependencies
└── README.md                 # This file


🧠 How It Works
User Input: Enter your travel question via chat (e.g. "Plan me a 5-day trip to Paris").

LLM Output: For full itineraries, a day-wise plan is generated and displayed with weather, cost, activities, and notes.

📸 Sample Output

🗺️ Travel Itinerary
📌 Summary: Barcelona Discovery: A 5-day trip exploring iconic landmarks, architecture, and cuisine.
💰 Total Cost: 840 EUR

📅 Detailed Plan:
Day 1, 2025-06-20, Friday:
   🏨 Check in at top-rated hotel
   🎒 Visit to Sagrada Familia
   🍽️ Dinner at a tapas restaurant
   🌤️ Weather: Sunny, 23.2°C to 28.1°C
   📝 Notes: Book tickets in advance


🔧 Setup Instructions
Clone the repo


git clone https://github.com/IpsheetaSahoo/AgenticAI_1.git

cd langgraph

cd Projects

cd aI_travel_planner

Install dependencies

pip install -r requirements.txt
Set up .env


SERPER_API_KEY=your_serper_api_key
OPENAI_API_KEY=your_openai_key  # if using LLM
Run Streamlit App

streamlit run app.py


📸 UI Preview


![image](https://github.com/user-attachments/assets/9ee39564-e1d3-4aec-8107-6874dd658a45)
