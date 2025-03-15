from agno import Agent, KnowledgeBase
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

# Initialize the knowledge base
kb = KnowledgeBase()

# Define the travel planning prompt
TRAVEL_AGENT_PROMPT = """You are an elite travel planning expert with decades of experience in crafting personalized travel experiences. Your expertise spans luxury, budget, corporate, adventure, cultural, and food-focused travel.

Your task is to create a comprehensive travel plan based on the provided requirements. Consider the following aspects:

1. Initial Assessment:
- Analyze group size, dynamics, and special needs
- Consider trip dates, duration, and budget constraints
- Account for must-see attractions and seasonal factors

2. Destination Research:
- Provide up-to-date information about attractions
- Include operating hours and availability
- Consider local events and weather patterns

3. Accommodation Planning:
- Recommend suitable accommodations based on travel style
- Consider location proximity to key attractions
- Balance comfort, convenience, and budget
- Include amenities and booking requirements

4. Activity Curation:
- Create a balanced mix of activities based on interests
- Optimize travel time between activities
- Include booking requirements and best times
- Provide insider tips for each activity

5. Logistics & Transportation:
- Detail transit options and transfer times
- Include cost estimates and duration
- Provide local transport tips
- Include emergency plans

6. Budget Breakdown:
- Itemize major expenses
- Suggest budget-friendly alternatives
- Highlight hidden costs
- Provide money-saving tips

For each recommendation, consider:
- Travel style (luxury/budget/corporate/adventure/cultural/food)
- Group size and dynamics
- Special requirements (dietary, mobility)
- Seasonal factors
- Local customs and etiquette
- Safety considerations
- Accessibility requirements

Your response should be structured, detailed, and include:
- Day-by-day itinerary
- Accommodation recommendations
- Activity suggestions with timing
- Transportation options
- Budget breakdown
- Emergency contacts
- Weather considerations
- Local tips and recommendations

Remember to:
- Optimize the experience within budget constraints
- Consider group dynamics and special needs
- Provide flexible options and backup plans
- Include booking requirements and deadlines
- Offer insider tips for a smoother experience"""

class TravelAgent:
    def __init__(self):
        self.agent = Agent(
            prompt=TRAVEL_AGENT_PROMPT,
            knowledge_base=kb,
            model="gpt-4-turbo-preview"
        )
        
        # Initialize knowledge base with travel data
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with travel-related information"""
        # Add general travel knowledge
        kb.add_text("""
        Travel Planning Best Practices:
        1. Always consider local customs and etiquette
        2. Include buffer time between activities
        3. Have backup plans for weather-dependent activities
        4. Consider time zones and jet lag
        5. Include emergency contacts and medical information
        """)
        
        # Add budget optimization tips
        kb.add_text("""
        Budget Optimization Tips:
        1. Book flights and accommodations in advance
        2. Consider off-peak travel times
        3. Use local transportation instead of taxis
        4. Look for free attractions and activities
        5. Eat at local restaurants instead of tourist spots
        """)
        
        # Add more specialized knowledge as needed
    
    async def create_travel_plan(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive travel plan using the AI agent"""
        # Format the request data for the agent
        prompt = f"""
        Create a detailed travel plan for:
        Destination: {request_data['destination']}
        Dates: {request_data['start_date']} to {request_data['end_date']}
        Group Size: {request_data['group_size']}
        Budget per Person: ${request_data['budget_per_person']}
        Travel Style: {request_data['preferences']['travel_style']}
        Interests: {', '.join(request_data['preferences']['interests'])}
        Dietary Restrictions: {', '.join(request_data['preferences']['dietary_restrictions'])}
        Special Requirements: {request_data['preferences']['mobility_requirements']}
        Must-See Attractions: {', '.join(request_data['must_see_attractions'])}
        """
        
        # Get response from the agent
        response = await self.agent.generate(prompt)
        
        # Parse and structure the response
        try:
            # Convert the response to structured data
            plan = self._parse_agent_response(response)
            return plan
        except Exception as e:
            raise Exception(f"Failed to parse agent response: {str(e)}")
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse the agent's response into structured data"""
        # TODO: Implement proper parsing logic
        # This is a placeholder implementation
        return {
            "trip_summary": response[:200],  # First 200 characters as summary
            "accommodations": [],
            "daily_itineraries": [],
            "total_budget": 0.0,
            "tips_and_recommendations": [],
            "emergency_contacts": {},
            "weather_forecast": {}
        } 