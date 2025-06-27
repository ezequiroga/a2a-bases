from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Task
from a2a.utils import new_task, new_agent_text_message
import json
from typing import Dict, List, Optional
from datetime import datetime


class EmployeeFlightRequestDatabase:
    """In-memory database for employee flight request management."""
    
    def __init__(self):
        self.flight_requests = [
            {
                "id": 1,
                "name": "John Smith",
                "departure": "Madrid",
                "destination": "London",
                "date": "2025-09-15",
                "flight_booking": {"flight": "IB6273", "seat": "12A", "gate": "B15", "purchased": True}
            },
            {
                "id": 2,
                "name": "Maria Garcia",
                "departure": "Barcelona",
                "destination": "Paris",
                "date": "2025-08-20",
                "flight_booking": {"flight": "VY2204", "seat": "8C", "gate": "A12", "purchased": True}
            },
            {
                "id": 3,
                "name": "Robert Johnson",
                "departure": "New York",
                "destination": "Los Angeles",
                "date": "2025-12-01",
                "flight_booking": None
            },
            {
                "id": 4,
                "name": "Anna Thompson",
                "departure": "London",
                "destination": "Dublin",
                "date": "2025-10-05",
                "flight_booking": None
            },
            {
                "id": 5,
                "name": "Carlos Rodriguez",
                "departure": "Tokyo",
                "destination": "Seoul",
                "date": "2025-11-10",
                "flight_booking": {"flight": "JL316", "seat": "15F", "gate": "C20", "purchased": True}
            },
            {
                "id": 6,
                "name": "Sophie Martin",
                "departure": "Paris",
                "destination": "Rome",
                "date": "2025-07-12",
                "flight_booking": None
            },
            {
                "id": 7,
                "name": "Michael Brown",
                "departure": "Rome",
                "destination": "Athens",
                "date": "2025-10-15",
                "flight_booking": {"flight": "AZ610", "seat": "22B", "gate": "D8", "purchased": True}
            },
            {
                "id": 8,
                "name": "Elena Popov",
                "departure": "Berlin",
                "destination": "Amsterdam",
                "date": "2025-11-18",
                "flight_booking": None
            },
            {
                "id": 9,
                "name": "Ahmed Hassan",
                "departure": "Dubai",
                "destination": "Mumbai",
                "date": "2025-12-20",
                "flight_booking": {"flight": "EK201", "seat": "6A", "gate": "E15", "purchased": True}
            },
            {
                "id": 10,
                "name": "Lisa Anderson",
                "departure": "Sydney",
                "destination": "Melbourne",
                "date": "2025-08-25",
                "flight_booking": None
            }
        ]
    
    def get_pending_requests(self) -> List[Dict]:
        """Get flight requests that are not yet booked."""
        return [request for request in self.flight_requests if request["flight_booking"] is None]
    
    def get_booked_requests(self) -> List[Dict]:
        """Get flight requests that are already booked."""
        return [request for request in self.flight_requests if request["flight_booking"] is not None]
    
    def find_request_by_name(self, name: str) -> Optional[Dict]:
        """Find a flight request by employee name."""
        for request in self.flight_requests:
            if request["name"].lower() == name.lower():
                return request
        return None


class EmployeeFlightRequestAgent:
    """Agent specialized in employee flight request management and status checking."""
    
    def __init__(self):
        """Initialize the agent with in-memory flight request database."""
        self.db = EmployeeFlightRequestDatabase()
        print(f"✅ Initialized flight request database with {len(self.db.flight_requests)} records")
    
    async def invoke(self, query: str = None) -> str:
        """
        Main method to invoke ticket operations.
        
        Args:
            context: Request context
            event_queue: Event queue for messages
            query: Query string
            
        Returns:
            String with operation results
        """
        query_lower = query.lower()
        
        if "pending" in query_lower or "left" in query_lower or "available" in query_lower or "not booked" in query_lower:
            result = await self.list_pending_requests()
            return result
        elif "booked" in query_lower or "taken" in query_lower or "purchased" in query_lower or "confirmed" in query_lower:
            result = await self.list_booked_requests()
            return result
        else:
            result = await self.check_employee_request(query)
            return result
    
    async def list_pending_requests(self) -> str:
        """
        List all flight requests that are not yet booked.
        
        Returns:
            String with formatted list of pending flight requests
        """
        pending_requests = self.db.get_pending_requests()
        
        if not pending_requests:
            return "✅ All employee flight requests have been booked!"
        
        result_lines = [f"⏳ PENDING FLIGHT REQUESTS ({len(pending_requests)} remaining):", ""]
        
        for request in pending_requests:
            result_lines.extend([
                f"  • {request['name']}",
                f"    🛫 Route: {request['departure']} → {request['destination']}",
                f"    📅 Date: {request['date']}",
                "    📋 Status: Awaiting booking",
                ""
            ])
        
        return "\n".join(result_lines)
    
    async def list_booked_requests(self) -> str:
        """
        List all flight requests that have been booked.
        
        Returns:
            String with formatted list of booked flight requests
        """
        booked_requests = self.db.get_booked_requests()
        
        if not booked_requests:
            return "📭 No employee flight requests have been booked yet."
        
        result_lines = [f"✈️ BOOKED FLIGHT REQUESTS ({len(booked_requests)} confirmed):", ""]
        
        for request in booked_requests:
            booking_info = request['flight_booking']
            result_lines.extend([
                f"  • {request['name']}",
                f"    🛫 Route: {request['departure']} → {request['destination']}",
                f"    📅 Date: {request['date']}",
                f"    ✈️ Flight: {booking_info['flight']}",
                f"    💺 Seat: {booking_info['seat']}",
                f"    🚪 Gate: {booking_info['gate']}",
                ""
            ])
        
        return "\n".join(result_lines)
    
    async def check_employee_request(self, query: str) -> str:
        """
        Check flight request status for a specific employee.
        
        Args:
            employee_name: Name of the employee to check
            
        Returns:
            String with employee's flight request status
        """
        request = self.db.find_request_by_name(query)
        
        if not request:
            return f"❌ No flight request found for '{query}'"
        
        if request["flight_booking"] is None:
            return f"⏳ {request['name']} has a pending flight request that is not booked yet.\n" \
                   f"🛫 Route: {request['departure']} → {request['destination']}\n" \
                   f"📅 Date: {request['date']}"
        else:
            booking_info = request["flight_booking"]
            return f"✅ {request['name']} has a booked flight!\n" \
                   f"🛫 Route: {request['departure']} → {request['destination']}\n" \
                   f"📅 Date: {request['date']}\n" \
                   f"✈️ Flight: {booking_info['flight']}\n" \
                   f"💺 Seat: {booking_info['seat']}\n" \
                   f"🚪 Gate: {booking_info['gate']}"


class EmployeeFlightRequestAgentExecutor(AgentExecutor):
    """Employee flight request management agent executor."""

    def __init__(self):
        self.agent = EmployeeFlightRequestAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()

        response = await self.agent.invoke(query)
        
        await event_queue.enqueue_event(new_agent_text_message(response))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        await event_queue.enqueue_event(new_agent_text_message("❌ Flight request operation cancelled"))
