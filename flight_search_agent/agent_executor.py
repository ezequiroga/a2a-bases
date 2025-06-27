"""
This file contains the FlightSearchAgent class, used for real-time flight search with push notification capabilities.
"""
import os
import uuid
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task
from a2a.types import Part, TextPart, TaskState, Task, Message, Role, TaskStatus

load_dotenv()

AVIATION_STACK_API_KEY = os.getenv("AVIATION_STACK_API_KEY")
AVIATION_STACK_BASE_URL = "https://api.aviationstack.com/v1/flightsFuture"

if not AVIATION_STACK_API_KEY:
    raise ValueError("AVIATION_STACK_API_KEY environment variable must be set in .env file")

USE_MOCK_DATA = False


def call_aviation_stack_api(iata_code: str, date: str, flight_type: str = "departure") -> Dict:
    """
    Perform the Aviation Stack API call.
    
    Args:
        iata_code: Airport IATA code (e.g., 'AEP', 'JFK', 'LAX')
        date: Flight date in YYYY-MM-DD format
        flight_type: Type of flight search - 'departure' or 'arrival'
    
    Returns:
        Dict with API response data
    """
    if USE_MOCK_DATA:
        return {
            "data": [
                {
                    "airline": {"name": "delta air lines", "iataCode": "dl"},
                    "flight": {"number": "7602", "iataNumber": "dl7602"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "17", "scheduledTime": "21:30"},
                    "arrival": {"iataCode": "gru", "terminal": "2", "gate": "104", "scheduledTime": "00:15"},
                    "aircraft": {"modelCode": "b738", "modelText": "boeing 737 max 8"},
                    "codeshared": {"airline": {"name": "aerolineas argentinas"}, "flight": {"iataNumber": "ar1250"}}
                },
                {
                    "airline": {"name": "gol", "iataCode": "g3"},
                    "flight": {"number": "3007", "iataNumber": "g33007"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "17", "scheduledTime": "21:30"},
                    "arrival": {"iataCode": "gru", "terminal": "2", "gate": "104", "scheduledTime": "00:15"},
                    "aircraft": {"modelCode": "b738", "modelText": "boeing 737 max 8"},
                    "codeshared": {"airline": {"name": "aerolineas argentinas"}, "flight": {"iataNumber": "ar1250"}}
                },
                {
                    "airline": {"name": "aerolineas argentinas", "iataCode": "ar"},
                    "flight": {"number": "1250", "iataNumber": "ar1250"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "17", "scheduledTime": "21:30"},
                    "arrival": {"iataCode": "gru", "terminal": "2", "gate": "104", "scheduledTime": "00:15"},
                    "aircraft": {"modelCode": "b738", "modelText": "boeing 737 max 8"}
                },
                {
                    "airline": {"name": "latam airlines", "iataCode": "la"},
                    "flight": {"number": "424", "iataNumber": "la424"},
                    "departure": {"iataCode": "aep", "terminal": "1", "gate": "16", "scheduledTime": "21:05"},
                    "arrival": {"iataCode": "scl", "terminal": "2", "gate": "", "scheduledTime": "22:29"},
                    "aircraft": {"modelCode": "a320", "modelText": "airbus a320-214"}
                },
                {
                    "airline": {"name": "latam airlines", "iataCode": "la"},
                    "flight": {"number": "5963", "iataNumber": "la5963"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "2", "scheduledTime": "19:30"},
                    "arrival": {"iataCode": "cor", "terminal": "t1", "gate": "7", "scheduledTime": "21:00"},
                    "aircraft": {"modelCode": "e190", "modelText": "embraer e190ar"},
                    "codeshared": {"airline": {"name": "aerolineas argentinas"}, "flight": {"iataNumber": "ar1552"}}
                },
                {
                    "airline": {"name": "aerolineas argentinas", "iataCode": "ar"},
                    "flight": {"number": "1552", "iataNumber": "ar1552"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "2", "scheduledTime": "19:30"},
                    "arrival": {"iataCode": "cor", "terminal": "t1", "gate": "7", "scheduledTime": "21:00"},
                    "aircraft": {"modelCode": "e190", "modelText": "embraer e190ar"}
                },
                {
                    "airline": {"name": "gol", "iataCode": "g3"},
                    "flight": {"number": "3107", "iataNumber": "g33107"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "", "scheduledTime": "22:35"},
                    "arrival": {"iataCode": "crd", "terminal": "", "gate": "", "scheduledTime": "01:10"},
                    "aircraft": {"modelCode": "e190", "modelText": "embraer e190ar"},
                    "codeshared": {"airline": {"name": "aerolineas argentinas"}, "flight": {"iataNumber": "ar1836"}}
                },
                {
                    "airline": {"name": "latam airlines", "iataCode": "la"},
                    "flight": {"number": "8316", "iataNumber": "la8316"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "", "scheduledTime": "22:35"},
                    "arrival": {"iataCode": "crd", "terminal": "", "gate": "", "scheduledTime": "01:10"},
                    "aircraft": {"modelCode": "e190", "modelText": "embraer e190ar"},
                    "codeshared": {"airline": {"name": "aerolineas argentinas"}, "flight": {"iataNumber": "ar1836"}}
                },
                {
                    "airline": {"name": "aerolineas argentinas", "iataCode": "ar"},
                    "flight": {"number": "1836", "iataNumber": "ar1836"},
                    "departure": {"iataCode": "aep", "terminal": "ta", "gate": "", "scheduledTime": "22:35"},
                    "arrival": {"iataCode": "crd", "terminal": "", "gate": "", "scheduledTime": "01:10"},
                    "aircraft": {"modelCode": "e190", "modelText": "embraer e190ar"}
                },
                {
                    "airline": {"name": "sky airline", "iataCode": "h2"},
                    "flight": {"number": "536", "iataNumber": "h2536"},
                    "departure": {"iataCode": "aep", "terminal": "", "gate": "8", "scheduledTime": "21:55"},
                    "arrival": {"iataCode": "scl", "terminal": "1", "gate": "", "scheduledTime": "23:25"},
                    "aircraft": {"modelCode": "a20n", "modelText": "airbus a320-251n"}
                }
            ]
        }
    else:
        params = {
            'access_key': AVIATION_STACK_API_KEY,
            'iataCode': iata_code.upper(),
            'type': flight_type,
            'date': date
        }
        
        print(f"🔍 Making real API call to Aviation Stack: {flight_type}s from {iata_code.upper()} on {date}")
        response = requests.get(AVIATION_STACK_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()


@tool(return_direct=True)
def search_flights_tool(iata_code: str, date: str, flight_type: str = "departure") -> str:
    """
    Search for flights using Aviation Stack API.
    
    Args:
        iata_code: Airport IATA code (e.g., 'AEP', 'JFK', 'LAX')
        date: Flight date in YYYY-MM-DD format (e.g., '2025-11-02')
        flight_type: Type of flight search - 'departure' or 'arrival' (default: 'departure')
    
    Returns:
        JSON string with flight search results
    """
    try:
        if not iata_code or len(iata_code) != 3:
            return "❌ Error: IATA code is required and must be exactly 3 characters (e.g., 'AEP', 'JFK')"
 
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return "❌ Error: Date is required and must be in YYYY-MM-DD format (e.g., '2025-11-20')"
        
        print(f"🔍 Searching flights: {flight_type}s from {iata_code.upper()} on {date}")
        
        api_data = call_aviation_stack_api(iata_code, date, flight_type)
        
        if 'data' not in api_data:
            message = f"❌ Error: Invalid API response format"
            print(message)
            return message
        
        flights = api_data['data']
        total_flights = len(flights)
        
        if total_flights == 0:
            message = f"📭 No {flight_type} flights found for {iata_code.upper()} on {date}"
            print(message)
            return message
        else:
            print(f"✅ {total_flights} {flight_type} flights found for {iata_code.upper()} on {date}")
        
        result = {
            "search_info": {
                "iata_code": iata_code.upper(),
                "date": date,
                "type": flight_type,
                "total_flights": 258 if USE_MOCK_DATA else total_flights
            },
            "flights": []
        }
        
        for flight in flights[:10]:
            flight_info = {
                "airline": {
                    "name": flight.get('airline', {}).get('name', 'Unknown'),
                    "iata_code": flight.get('airline', {}).get('iataCode', '')
                },
                "flight": {
                    "number": flight.get('flight', {}).get('number', ''),
                    "iata_number": flight.get('flight', {}).get('iataNumber', '')
                },
                "departure": {
                    "iata_code": flight.get('departure', {}).get('iataCode', ''),
                    "terminal": flight.get('departure', {}).get('terminal', ''),
                    "gate": flight.get('departure', {}).get('gate', ''),
                    "scheduled_time": flight.get('departure', {}).get('scheduledTime', '')
                },
                "arrival": {
                    "iata_code": flight.get('arrival', {}).get('iataCode', ''),
                    "terminal": flight.get('arrival', {}).get('terminal', ''),
                    "gate": flight.get('arrival', {}).get('gate', ''),
                    "scheduled_time": flight.get('arrival', {}).get('scheduledTime', '')
                },
                "aircraft": {
                    "model_code": flight.get('aircraft', {}).get('modelCode', ''),
                    "model_text": flight.get('aircraft', {}).get('modelText', '')
                }
            }
            
            if flight.get('codeshared'):
                flight_info["codeshared"] = {
                    "airline_name": flight.get('codeshared', {}).get('airline', {}).get('name', ''),
                    "flight_number": flight.get('codeshared', {}).get('flight', {}).get('iataNumber', '')
                }

            result["flights"].append(flight_info)

        message = json.dumps(result, indent=2)
        return message

    except Exception as e:
        message = f"❌ Error searching flights: {str(e)}"
        print(message)
        return message


class FlightSearchAgent:
    """ReAct agent specialized in flight search with push notification capabilities."""
    
    def __init__(self):
        """Initialize the ReAct agent with tools."""
        self.tools = [search_flights_tool]
        
        self.model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0
        )
        
        self.memory = MemorySaver()
        
        system_prompt = """You are a Flight Search Agent specialized in finding flights using real-time aviation data.

Your capabilities:
1. Search for flights using the search_flights_tool with airport IATA codes and dates

Instructions:
- Show ALL flights returned by the tool, do not filter or summarize
- Display every single flight in the results
- Do not limit the number of flights shown
- Always search for DEPARTURE flights unless specifically asked for arrivals
- Use proper IATA codes (3 letters, e.g., AEP, JFK, LAX)
- Dates should be in YYYY-MM-DD format
- Extract IATA codes and dates from user queries intelligently
- Be helpful and provide clear, formatted responses about all the flight information
- Return all the information and the whole list of flights returned by the search_flights_tool
- Do not omit any information, do not summarize the results and do not truncate the results
- Do not ask follow-up questions, just return the results

For flight searches, focus on:
- Departure/arrival times
- Airlines and flight numbers
- Aircraft information
- Terminal and gate details (if available)
- Return at least 10 flights
- Match the results returned by the search_flights_tool with the flight destination and date for an accurate response
"""
        self.agent_graph = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.memory,
            prompt=system_prompt
        )
        
        print("✅ Initialized Flight Search ReAct Agent with Aviation Stack API")
    
    async def invoke(self, task_id: str, context_id: str, query: str = None) -> Message:
        """
        Main method to handle flight search requests using ReAct pattern.
        
        Args:
            task: Task object
            updater: Task updater for streaming messages
            query: User query for flight search
        """
        try:
            print("🤖 Processing your flight search request...")
            user_message = f"Return at least 10 flights for: {query}"
            print(f"🔍 User message: {user_message}")
            
            config = {"configurable": {"thread_id": task_id}}
            
            messages = [("user", user_message)]
            
            last_message = ""

            response = self.agent_graph.invoke(
                {"messages": messages},
                config=config
            )
            print("✅ Flight search completed!")

            last_message = response['messages'][-1].content
            
            final_response = last_message if last_message else "Flight search completed - check the results above."
            
            push_notification_payload = {
                "flights": final_response,
                "source": "flight_search_agent",
                "metadata": {"task_id": task_id, "context_id": context_id}
            }
            
            part = TextPart(text=json.dumps(push_notification_payload))
            message = Message(
                role=Role.agent,
                parts=[part],
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                contextId=context_id,
            )
            return message
            
        except Exception as e:
            error_msg = f"❌ Error occurred during flight search: {str(e)}"
            
            part = TextPart(text=error_msg)
            message = Message(
                role=Role.agent,
                parts=[part],
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                contextId=context_id,
            )
            return message


class FlightSearchAgentExecutor(AgentExecutor):
    """Flight search agent executor with ReAct capabilities."""

    def __init__(self):
        self.agent = FlightSearchAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute flight search request."""
        query = context.get_user_input()

        updater = TaskUpdater(event_queue, context.current_task.id, context.current_task.contextId)
        await updater.update_status(
            TaskState.submitted,
            new_agent_text_message(
                "🤖 Flight Search Agent activated...",
                context.current_task.contextId,
                context.current_task.id
            )
        )

        message = await self.agent.invoke(context.current_task.id, context.current_task.contextId, query)

        await updater.update_status(TaskState.working, message)
        await updater.update_status(TaskState.completed)

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel flight search operation."""
        await event_queue.enqueue_event(new_agent_text_message("❌ Flight search operation cancelled"))
