"""
utils/schemas.py

This module defines the Pydantic models used across the application, including:

- UserInput: Validated input schema for collecting user preferences such as 
  destination, trip dates, budget, and currency.

- TravelPlannerState: LangGraph state object used to persist data across the workflow,
  including user input, API outputs, cost breakdown, and itinerary.

These models ensure type safety, structured data passing between tools and nodes, 
and serve as the backbone for LangChain's tool schema validation.

Exports:
- UserInput
- TravelPlannerState
"""


from pydantic import BaseModel, Field, field_validator
from typing import Literal
from typing import Optional, List, Dict, Any
from datetime import date

class BudgetRange(BaseModel):
    min: int = Field(..., ge=0, description="Minimum budget in user's currency")
    max: int = Field(..., ge=0, description="Maximum budget in user's currency")

    @field_validator("max")
    @classmethod
    def check_max_greater_than_min(cls, v: int, info)-> int:
        min_value = info.data.get("min")
        if min_value is not None and v < min_value:
            raise ValueError("Maximum budget must be greater than or equal to minimum budget")
        return v

class UserInput(BaseModel):
    destination_city: str = Field(..., description="Name of the city to travel")
    start_date: date = Field(..., description="Start date of the trip")
    end_date: date = Field(..., description="End date of the trip")
    budget_range: BudgetRange
    native_currency: Literal["USD", "EUR", "INR", "GBP", "JPY", "CAD", "AUD"]  # Extend as needed
    raw_query: str = Field(..., description="Raw user query for context")
    query_intent: Optional[str]

    @field_validator("end_date")
    @classmethod
    def check_dates(cls, v: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("End date must be after start date")
        return v

class TravelPlannerState(BaseModel):
    # Core user input
    user_input: Optional[UserInput] = Field(None, description="Validated input from the user")

    # Real-time data fetched during planning
    weather_data: Optional[Dict[str, Any]] = Field(default=None, description="Weather forecast")
    attractions_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of attractions")
    hotels_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of hotels and prices")
    itinerary_data: Optional[dict] =  Field(default=None, description="Generated itinerary data")

    # Processed outputs
    converted_costs: Optional[Dict[str, float]] = Field(default=None, description="Converted costs")
    total_cost: Optional[float] = Field(default=None, description="Final estimated total cost")
    daily_budget: Optional[float] = Field(default=None, description="Daily budget")
    itinerary: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structured itinerary")
    summary: Optional[str] = Field(default=None, description="Final summary of the travel plan")

    class Config:
        arbitrary_types_allowed = True






    
