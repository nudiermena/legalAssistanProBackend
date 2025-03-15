from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import uvicorn
from travel_agent import TravelAgent

app = FastAPI(
    title="Globe Hopper AI Agent",
    description="An elite travel planning expert API that creates personalized travel experiences",
    version="1.0.0"
)

# Initialize the travel agent
travel_agent = TravelAgent()

class TravelStyle(str, Enum):
    LUXURY = "luxury"
    BUDGET = "budget"
    CORPORATE = "corporate"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    FOOD = "food"

class TravelerPreferences(BaseModel):
    travel_style: TravelStyle
    interests: List[str] = Field(..., description="List of traveler interests")
    dietary_restrictions: Optional[List[str]] = []
    mobility_requirements: Optional[str] = None
    special_requests: Optional[str] = None

class TripRequest(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    group_size: int
    budget_per_person: float
    preferences: TravelerPreferences
    must_see_attractions: Optional[List[str]] = []

class Accommodation(BaseModel):
    name: str
    type: str
    location: str
    price_per_night: float
    amenities: List[str]
    rating: float
    booking_link: Optional[str]

class Activity(BaseModel):
    name: str
    description: str
    duration: str
    price: float
    booking_required: bool
    best_time: str
    tips: List[str]

class Transportation(BaseModel):
    type: str
    description: str
    estimated_cost: float
    duration: str
    tips: List[str]

class DailyItinerary(BaseModel):
    day_number: int
    date: datetime
    activities: List[Activity]
    meals: Dict[str, str]
    transportation: List[Transportation]

class TravelPlan(BaseModel):
    trip_summary: str
    accommodations: List[Accommodation]
    daily_itineraries: List[DailyItinerary]
    total_budget: float
    tips_and_recommendations: List[str]
    emergency_contacts: Dict[str, str]
    weather_forecast: Optional[Dict[str, str]]

@app.post("/create-travel-plan", response_model=TravelPlan)
async def create_travel_plan(request: TripRequest):
    """
    Create a comprehensive travel plan based on the provided requirements.
    """
    try:
        # Convert the request to a dictionary
        request_data = request.model_dump()
        
        # Get the travel plan from the AI agent
        plan = await travel_agent.create_travel_plan(request_data)
        
        # Convert the plan to the expected response model
        return TravelPlan(**plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "Globe Hopper AI Agent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
