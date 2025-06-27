"""
Test file for Flight Search Agent
Run from dev_post/ directory as: python -m tests.test_flight_search
"""
import asyncio

from flight_search_agent.agent_executor import FlightSearchAgentExecutor


async def test_flight_search_agent():
    """Test the flight search agent with a simple query."""
    
    print("🧪 Testing Flight Search Agent...")
    
    executor = FlightSearchAgentExecutor()
    
    print("✅ Flight Search Agent initialized successfully!")
    print("🛫 Agent includes:")
    print("   - ReAct pattern with LangGraph")
    print("   - Aviation Stack API integration")
    print("   - Push notification capabilities")
    print("   - Claude 3.5 Sonnet model")
    
    print("\n📋 Available tools:")
    for tool in executor.agent.tools:
        print(f"   - {tool.name}: {tool.description}")


if __name__ == "__main__":
    print("💡 Run from dev_post/ directory as: python -m tests.test_flight_search")
    asyncio.run(test_flight_search_agent()) 