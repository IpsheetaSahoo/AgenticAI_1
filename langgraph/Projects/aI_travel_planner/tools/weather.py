# tools/weather.py

import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from langchain.tools import tool


@tool
def get_weather_forecast(location: str, start_date: str, end_date: str) -> dict:
    """
    Fetches the daily weather forecast for a given location and date range using the Open-Meteo API.

    Args:
        location (str): A human-readable place name (e.g., "Delhi, India").
        start_date (str): Forecast start date in 'YYYY-MM-DD' format.
        end_date (str): Forecast end date in 'YYYY-MM-DD' format.

    Returns:
        dict: JSON-style dictionary with forecast info or error message.

    Example Output:
        {
            "location": "Goa, India",
            "start_date": "2025-06-19",
            "end_date": "2025-06-22",
            "forecast": [
                {"date": "2025-06-19", "min_temp_c": 25.1, "max_temp_c": 32.3},
                {"date": "2025-06-20", "min_temp_c": 24.7, "max_temp_c": 31.9},
                ...
            ]
        }

    Notes:
        - Works up to 7 days from today.
        - Returns a list of daily temperature ranges.
    """
    try:
        # Validate dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Please provide dates in 'YYYY-MM-DD' format."}

        today = datetime.utcnow().date()
        max_forecast = today + timedelta(days=7)

        if start < today or end < today:
            return {"error": "Dates must not be in the past."}
        if end > max_forecast:
            return {"error": "Forecast is available for up to 7 days from today."}
        if end < start:
            return {"error": "End date must be after start date."}

        # Geocode location
        geolocator = Nominatim(user_agent="open_meteo_weather_tool")
        loc = geolocator.geocode(location)
        if not loc:
            return {"error": f"Could not find location: {location}"}

        lat, lon = loc.latitude, loc.longitude

        # API call
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
            f"&start_date={start}&end_date={end}"
        )
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": f"Failed to fetch weather data: {response.status_code}"}

        data = response.json().get("daily", {})
        if not data:
            return {"error": f"No weather data available for {location}."}

        # Prepare JSON forecast
        forecast_list = []
        for i in range(len(data["time"])):
            forecast_list.append({
                "date": data["time"][i],
                "min_temp_c": data["temperature_2m_min"][i],
                "max_temp_c": data["temperature_2m_max"][i],
            })

        return {
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "forecast": forecast_list
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
