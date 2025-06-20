
# tools/itinerary.py

"""
This tool aggregates weather, hotels, and attractions data,
estimates the total cost (converted to native currency),
and generates a day-wise itinerary using OpenAI and LangChain's Runnable chains.
"""

from langchain_core.tools import tool
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable

# Constants
AVG_DAILY_FOOD_COST = 30  # USD
AVG_DAILY_LOCAL_TRANSPORT = 10  # USD

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

@tool
def generate_itinerary(weather_data: dict, hotels_data: list, attractions_data: list,
                       start_date: str, end_date: str,
                       budget_range: dict, native_currency: str) -> dict:
    """
    Generates a structured day-wise itinerary using simplified data (title + link).
    """

    try:
        # 1. Trip duration
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        num_days = (end - start).days + 1

        # 2. Cost estimation
        hotel_cost = 100 * num_days  # No actual price in data, using rough avg
        food_cost = AVG_DAILY_FOOD_COST * num_days
        transport_cost = AVG_DAILY_LOCAL_TRANSPORT * num_days
        total_usd = hotel_cost + food_cost + transport_cost

        # 3. Currency conversion
        res = requests.get("https://api.exchangerate.host/convert", params={
            "from": "USD", "to": native_currency, "amount": total_usd
        })
        total_converted = res.json().get("result", total_usd)

        # 4. Format Inputs
        weather_str = "; ".join(
            f"date: {w['date']}, min_temp_c: {w['min_temp_c']}, max_temp_c: {w['max_temp_c']}"
            for w in weather_data.get("forecast", [])
        )

        hotels_str = "\n".join(
            f"{i+1}. {h['title']} 🔗 {h['link']}" for i, h in enumerate(hotels_data)
        )

        attractions_str = "\n".join(
            f"{i+1}. {a['title']} 🔗 {a['link']}" for i, a in enumerate(attractions_data)
        )

        # 5. Prompt template
        prompt = ChatPromptTemplate.from_template("""
You are a professional travel planner.

Create a realistic, well-balanced, and visually engaging 5-day travel itinerary for a trip based on the following input data.

📅 Start Date: {start_date}  
📅 End Date: {end_date}  
🌍 Destination: Based on the attractions and hotels listed  
⛅ Weather Forecast: {weather_data}  
🏨 Hotels:
{hotels_data}

🎯 Attractions:
{attractions_data}

💶 Estimated Budget: Around {total_cost} {currency}

📝 Requirements:
- Use hotel titles to assume check-in/check-out locations, one per night.
- Use attraction titles and links to guide scheduling of top sights (even if time or price is not available).
- Avoid specific assumptions not in the data. Instead, say "Visit to [Title]" or "Explore [Title]".
- Prioritize indoor attractions on cooler days (below 24°C) and outdoor ones on warmer days.
- Add meals (🍽️), hotel stays (🏨), and transfers (🚗) to each day's plan.
- Format output as valid JSON with:
  - summary: brief trip overview
  - detailed_itinerary: list of daily plans (day, date, destination, activities[], weather, notes)

Icons: 🏨 for hotel, 🎒 for activity, 🍽️ for meal, 🚗 for transfers.

EXAMPLE ATTRACTION ENTRY:
"🎒 Visit to Sagrada Familia (https://example.com)"

EXAMPLE HOTEL ENTRY:
"🏨 Stay at H10 Madison Hotel (https://example.com)"

EXAMPLE FORMAT:

```json
{{
  "summary": "Barcelona Discovery: A 5-day trip exploring iconic landmarks, architecture, and cuisine.",
  "detailed_itinerary": [
    {{
      "day": "Day 1",
      "date": "2025-06-20, Friday",
      "destination": "Barcelona",
      "activities": [
        {{
          "type": "hotel",
          "icon": "🏨",
          "description": "Check in at H10 Madison Hotel (https://example.com)"
        }},
        {{
          "type": "activity",
          "icon": "🎒",
          "description": "Visit to Sagrada Familia (https://example.com)"
        }},
        {{
          "type": "meal",
          "icon": "🍽️",
          "description": "Dinner at a local tapas restaurant"
        }}
      ],
      "weather": "Sunny, 23.1°C to 27.6°C",
      "notes": "Take metro from hotel; Book attraction tickets in advance"
    }}
  ]
}}
    """)

        parser = JsonOutputParser()
        model = ChatOpenAI(model="gpt-4o-mini")
        chain: Runnable = prompt | model | parser

        result = chain.invoke({
            "start_date": start_date,
            "end_date": end_date,
            "weather_data": weather_str,
            "hotels_data": hotels_str,
            "attractions_data": attractions_str,
            "total_cost": round(total_converted, 2),
            "currency": native_currency
        })

        return {
            "summary": result.get("summary"),
            "total_cost": round(total_converted, 2),
            "currency": native_currency,
            "detailed_itinerary": result.get("detailed_itinerary", [])
        }

    except Exception as e:
        return {"error": str(e)}
