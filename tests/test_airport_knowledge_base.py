#!/usr/bin/env python3
"""
Test script for the airport knowledge base function
Run from dev_post/ directory as: python -m tests.test_airport_knowledge_base
"""
import asyncio
import uuid

from airport_knowledge_base_agent.agent_executor import AirportKnowledgeBaseAgent
from a2a.types import Task, TaskStatus, TaskState

class MockTaskUpdater:
    """Mock TaskUpdater for testing"""
    def __init__(self):
        self.events = []

    async def update_status(self, state, message=None):
        """Mock update_status that prints the message"""
        if message and hasattr(message, 'parts') and message.parts:
            content = message.parts[0].text if hasattr(message.parts[0], 'text') else str(message.parts[0])
            print(f"📨 {content}")
        self.events.append((state, message))
    
    async def complete(self, message=None):
        """Mock complete that prints the final message"""
        if message and hasattr(message, 'parts') and message.parts:
            content = message.parts[0].text if hasattr(message.parts[0], 'text') else str(message.parts[0])
            print(f"✅ Final result: {content}")
        self.events.append(("completed", message))

async def test_lookup():
    """Test function for airport knowledge base lookup"""
    agent = AirportKnowledgeBaseAgent()
    
    test_queries = [
        "Madrid",
        "Barcelona", 
        "New York",
        "London",
        "Tokyo",
        "Buenos Aires"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"TESTING KNOWLEDGE BASE LOOKUP: {query}")
        print('='*50)
        
        task = Task(
            id=str(uuid.uuid4()),
            contextId=str(uuid.uuid4()),
            status=TaskStatus(state=TaskState.submitted)
        )
        
        updater = MockTaskUpdater()
        
        await agent.invoke(task, updater, query)
        print()

if __name__ == "__main__":
    print("📚 Testing the airport knowledge base function...")
    print("💡 Run from dev_post/ directory as: python -m tests.test_airport_knowledge_base")
    asyncio.run(test_lookup())
