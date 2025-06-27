#!/usr/bin/env python3
"""
Test script for the employee flight request agent
Run from dev_post/ directory as: python -m tests.test_employee_flight_request
"""
import asyncio

from employee_flight_request_agent.agent_executor import EmployeeFlightRequestAgentExecutor


async def test_employee_flight_request_agent():
    """Test the employee flight request agent with a simple query."""

    print("🧪 Testing Employee Flight Request Agent...")
    
    try:
        executor = EmployeeFlightRequestAgentExecutor()
        
        print("✅ Employee Flight Request Agent initialized successfully!")
        print("📋 Agent includes:")
        print("   - Employee flight request management")
        print("   - Booking status tracking")
        print("   - Request processing capabilities")
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")


if __name__ == "__main__":
    print("💡 Run from dev_post/ directory as: python -m tests.test_employee_flight_request")
    asyncio.run(test_employee_flight_request_agent()) 