"""
ReAct Agent with A2A Protocol Integration using LangGraph
This agent can interact with A2A agents using tools and streaming.
Now includes HTTP endpoint for receiving external flight findings.
"""
import asyncio
import json
import logging
import os
import select
import sys
import threading
import uvicorn
from datetime import datetime
from queue import Queue
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Message,
    TextPart,
    Role,
    TaskState,
    PushNotificationConfig,
    TaskPushNotificationConfig,
    SetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigRequest,
    TaskIdParams,
    MessageSendConfiguration,
    GetTaskRequest,
    Task,
)

load_dotenv()

FLIGHTS_ENDPOINT_PATH = "/api/flights-findings"
HTTP_SERVER_PORT = 9990

class InternalMessage:
    """Internal message class for queue processing."""
    def __init__(self, user_input: str, thread_id: str, source: str, timestamp: str, metadata: Optional[Dict[str, Any]] = None):
        self.user_input = user_input
        self.thread_id = thread_id
        self.source = source
        self.timestamp = timestamp
        self.metadata = metadata or {}


class A2AAgentRegistry:
    """Mock registry for A2A agents. Later will be replaced with real discovery."""
    
    def __init__(self):
        self.agents = {
            "airport_knowledge_base": {
                "name": "Airport Knowledge Base Agent",
                "description": "Knowledge base for airport information and city-airport mappings",
                "base_url": "http://localhost:9991",
                "capabilities": ["airport_lookup", "city_airport_mapping"],
                "card": None,
                "client": None
            },
            "employee_flight_requests": {
                "name": "Employee Flight Request Agent", 
                "description": "Check employee flight requests and booking status",
                "base_url": "http://localhost:9992",
                "capabilities": ["flight_request_check", "booking_lookup"],
                "card": None,
                "client": None
            },
            "flight_search": {
                "name": "Flight Search Agent",
                "description": "Scheduled flight search using Aviation Stack",
                "base_url": "http://localhost:9993",
                "capabilities": ["flight_search"],
                "card": None,
                "client": None
            }
        }
    
    async def initialize_agents(self, httpx_client: httpx.AsyncClient):
        """Initialize A2A clients for all registered agents."""
        for _, agent_info in self.agents.items():
            try:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=agent_info["base_url"]
                )
                
                try:
                    card: AgentCard = await resolver.get_agent_card()
                    client = A2AClient(httpx_client=httpx_client, agent_card=card)
                    
                    agent_info["card"] = card
                    agent_info["client"] = client
                    print(f"✅ Initialized {agent_info['name']} at {agent_info['base_url']}")
                    print(f"   📝 Description: {agent_info['description']}")
                    
                except Exception as e:
                    print(f"⚠️  Could not connect to {agent_info['name']} at {agent_info['base_url']}: {e}")
                    agent_info["card"] = None
                    agent_info["client"] = None
                    
            except Exception as e:
                print(f"❌ Failed to initialize {agent_info['name']}: {e}")
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent info by ID."""
        return self.agents.get(agent_id)
    
    def list_available_agents(self) -> List[str]:
        """List all agents that are available (have active clients)."""
        return [
            agent_id for agent_id, info in self.agents.items() 
            if info["client"] is not None
        ]


class AirportKnowledgeTool(BaseTool):
    """
    Tool to retrieve airport information from the knowledge base.

    This tool must be used when users ask about airport names or need to find airports in specific cities.

    The tool receives the name of an airport or city and returns the correct airport names and city-airport mappings.
    The tool returns the name of the airport, city, country, and IATA code from the knowledge base.
    """
    
    name: str = "airport_knowledge_base"
    description: str = "Retrieve airport information from knowledge base. Use this when users ask about airport names or airports in specific cities."
    agent_registry: A2AAgentRegistry = None
    return_direct: bool = False
    
    def __init__(self, agent_registry: A2AAgentRegistry):
        super().__init__(agent_registry=agent_registry)
    
    async def _arun(self, query: str) -> str:
        """Async implementation to call the airport knowledge base agent."""
        agent_info = self.agent_registry.get_agent("airport_knowledge_base")
        
        if not agent_info or not agent_info["client"]:
            return "❌ Airport knowledge base agent is not available. Please check if the service is running."
        
        try:
            part = TextPart(text=query)
            message = Message(
                role=Role.user,
                parts=[part],
                messageId=str(uuid4()),
            )
            
            streaming_request = SendStreamingMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(message=message)
            )
            
            client = agent_info["client"]
            stream_response = client.send_message_streaming(streaming_request)
            
            full_response = ""
            print(f"\n📚 Looking up airport information for: {query}")
            
            async for chunk in stream_response:
                json_chunk = chunk.model_dump(mode='json', exclude_none=True)
                if json_chunk['result']['status']['state'] == TaskState.completed:
                    full_response = f"\n✅ Knowledge base lookup completed\n{json_chunk['result']['status']['message']['parts'][0]['text']}\n"
                    break
                else:
                    print(f"📨 {json_chunk['result']['status']['message']['parts'][0]['text']}\n")
            
            return full_response if full_response else "✅ Knowledge base lookup completed - check the streaming output above."
            
        except Exception as e:
            return f"❌ Error calling airport knowledge base agent: {str(e)}"

    def _run(self, query: str) -> str:
        """Sync wrapper (not used in async context)."""
        return asyncio.run(self._arun(query))


class EmployeeFlightRequestTool(BaseTool):
    """
    Tool to check the status of employee flight requests.

    This tool must be used when users ask about the status of employee flight requests.

    The tool must receive the employee name or request type and return whether the employee has flight requests or not.
    If the employee has flight requests, the tool must return the status of the requests.
    If the employee does not have flight requests, the tool must return a message saying that the employee does not have flight requests.
    """
    
    name: str = "employee_flight_requests"
    description: str = "Check employee flight requests, bookings, or request status. Use when users ask about their flight requests or bookings."
    agent_registry: A2AAgentRegistry = None
    
    def __init__(self, agent_registry: A2AAgentRegistry):
        super().__init__(agent_registry=agent_registry)
    
    async def _arun(self, query: str) -> str:
        """Async implementation to call the employee flight request agent."""
        agent_info = self.agent_registry.get_agent("employee_flight_requests")
        
        if not agent_info or not agent_info["client"]:
            return "❌ Employee flight request agent is not available. Please check if the service is running."
        
        try:
            part = TextPart(text=query)
            message = Message(
                role=Role.user,
                parts=[part],
                messageId=str(uuid4()),
            )
            
            send_message_payload = MessageSendParams(message=message)

            request = SendMessageRequest(
                id=str(uuid4()), 
                params=send_message_payload,
            )
            
            print(f"\n📋 Checking flight requests for: {query}")
            client = agent_info["client"]
            return await client.send_message(request)
            
        except Exception as e:
            return f"❌ Error calling employee flight request agent: {str(e)}"
    
    def _run(self, query: str) -> str:
        """Sync wrapper (not used in async context)."""
        return asyncio.run(self._arun(query))


class FlightSearchTool(BaseTool):
    """
    Tool to search for flights using scheduled flights data.

    This tool must be used when users ask about flight searches, flight availability, or want to find flights.

    The tool receives airport IATA codes and dates to search for flights using Aviation Stack API.
    It returns scheduled flights data including airlines, flight numbers, schedules, and aircraft details.
    """
    
    name: str = "flight_search"
    description: str = "Search for scheduled flights by airport IATA code and date. Use when users want to find flights or check flight availability."
    agent_registry: A2AAgentRegistry = None
    flight_search_callback_url: str = f"http://localhost:{HTTP_SERVER_PORT}{FLIGHTS_ENDPOINT_PATH}"  # TODO: do not hardcode the callback URL

    def __init__(self, agent_registry: A2AAgentRegistry):
        super().__init__(agent_registry=agent_registry)
    
    async def _arun(self, query: str) -> str:
        """Async implementation to call the flight search agent."""
        agent_info = self.agent_registry.get_agent("flight_search")
        
        if not agent_info or not agent_info["client"]:
            return "❌ Flight search agent is not available. Please check if the service is running."
        
        async def async_search():
            """Execute flight search asynchronously."""
            try:
                client: A2AClient = agent_info["client"]
                
                part = TextPart(text=query)
                message = Message(
                    role=Role.user,
                    parts=[part],
                    messageId=str(uuid4()),
                    contextId=str(uuid4()),
                    taskId=str(uuid4())
                )
                
                request = SendStreamingMessageRequest(
                    id=str(uuid4()),
                    params=MessageSendParams(
                        message=message,
                        configuration=MessageSendConfiguration(
                            acceptedOutputModes=["text"],
                            pushNotificationConfig=PushNotificationConfig(
                                url=self.flight_search_callback_url
                            )
                        )
                    )
                )
                
                response = client.send_message_streaming(request=request)
                
                async for chunk in response:
                    pass
                    
            except Exception as e:
                print(f"❌ Error in background flight search: {str(e)}")
        
        asyncio.create_task(async_search())
        
        print(f"🛫 Flight search initiated in background for: {query}")
        
        return "✅ Flight search initiated - results will be sent via push notification once completed"
            

    def _run(self, query: str) -> str:
        """Sync wrapper (not used in async context)."""
        return asyncio.run(self._arun(query))


class ReactChatAgent:
    """LangGraph ReAct agent that can interact with A2A agents through tools and receive external messages via HTTP."""
    
    def __init__(self):
        self.agent_registry = A2AAgentRegistry()

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
        
        self.model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            api_key=api_key
        )
        
        self.memory = MemorySaver()
        
        self.agent_graph = None
        
        self.external_message_queue = Queue()

        self.app = FastAPI(title="ReAct Chat Agent API", version="1.0.0")
        self.setup_http_endpoints()
    
    def setup_http_endpoints(self):
        """Setup HTTP endpoints for receiving external messages."""
        
        @self.app.post(FLIGHTS_ENDPOINT_PATH)
        async def receive_flight_findings(flight_finding: Task):
            """Receive flight findings and add them to the message queue."""
            try:
                if flight_finding.status.state != TaskState.completed:
                    return
                
                data_string = flight_finding.history[-1].parts[0].root.text
                outer_json = json.loads(data_string)
                flights_data = json.loads(outer_json["flights"])
                flights_list = flights_data["flights"]

                internal_msg = InternalMessage(
                    user_input=flights_list,
                    thread_id=f"flights_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    source="flight_findings",
                    timestamp=datetime.now().isoformat()
                )
                
                self.external_message_queue.put(internal_msg)
                
                return {
                    "status": "success",
                    "message": "Flight findings received and queued for processing",
                    "flights_count": len(flights_list),
                    "endpoint": FLIGHTS_ENDPOINT_PATH
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing flight findings: {str(e)}")
        

        @self.app.get("/api/status")
        async def get_status():
            """Get agent status and queue information."""
            return {
                "status": "active",
                "flights_endpoint": FLIGHTS_ENDPOINT_PATH,
                "queue_size": self.external_message_queue.qsize(),
                "available_agents": self.agent_registry.list_available_agents()
            }
        
    async def initialize(self, httpx_client: httpx.AsyncClient):
        """Initialize the agent and its tools."""
        print("🤖 Initializing LangGraph ReAct Chat Agent with Anthropic Claude...")
        
        await self.agent_registry.initialize_agents(httpx_client)
        
        tools = [
            AirportKnowledgeTool(self.agent_registry),
            EmployeeFlightRequestTool(self.agent_registry),
            FlightSearchTool(self.agent_registry)
        ]
        
        system_prompt = """You are a helpful assistant that manages employee flight requests in a corporate environment and can search for scheduled flights. Employees submit flight requests, and someone is responsible for booking them.

You have access to specialized tools:
1. airport_knowledge_base: Use this to retrieve airport information from the knowledge base when users ask about airport names or airports in specific cities.
2. employee_flight_requests: Use this to get the list of employee flight requests and their booking status.
3. flight_search: Use this to search for scheduled flights using Aviation Stack API when users want to find available flights.

Guidelines:
- Always use the appropriate tool when users ask about airports, flights, or employee flight requests
- Be friendly and helpful in your responses
- If a tool provides streamed output, acknowledge that the detailed results are shown above
- Provide clear and concise summaries of the tool results
- If you're unsure which tool to use, ask for clarification

Employee-specific queries:
- If you think the user is asking about a specific employee, ask for confirmation first
- If confirmed, use the employee_flight_requests tool with the employee's name to check their flight request status
- If the employee has pending flight requests, you can optionally use airport_knowledge_base to get information about airports for their route
- If the employee has booked flight requests, inform the user about the booking details
- If the employee has no flight requests (pending or booked), inform the user accordingly

Tool Usage Rules:
- For pending flight requests: use employee_flight_requests tool with "pending" in the query
- For booked flight requests: use employee_flight_requests tool with "booked" in the query  
- For specific employee requests: use employee_flight_requests tool with the employee's name in the query
- For airport information lookups: use airport_knowledge_base tool to get correct airport names or find airports in specific cities
- For flight searches: use flight_search tool with airport IATA codes and dates (e.g., "search flights from AEP on 2025-11-20")

Flight Search Guidelines:
- When users ask about finding flights, use the flight_search tool
- The tool expects airport IATA codes (3 letters) and dates in YYYY-MM-DD format
- Extract IATA codes and dates from user queries intelligently
- If users don't provide IATA codes, you can use airport_knowledge_base first to find the correct codes
- Flight search provides scheduled flights data including airlines, schedules, aircraft, and terminal information
- Flight search tool returns an empty message as the results are sent via push notifications to the HTTP endpoint once the search is completed
- Inform the user that the search is initiated and the results will be received via push notifications once the search is completed
- Returns all the flights found in the search
- Return at least 10 flights

External Messages:
- When you receive external messages (like flight findings), simply acknowledge and inform the user about the information received
- Do not take any actions or use tools when processing external messages
- Format the external message keeping the original structure, format and content

Remember: Your tools will provide detailed streaming output directly to the user, so focus on interpreting and summarizing the results clearly.
"""

        self.agent_graph = create_react_agent(
            model=self.model,
            tools=tools,
            checkpointer=self.memory,
            prompt=system_prompt
        )
        
        available_agents = self.agent_registry.list_available_agents()
        print(f"✅ LangGraph ReAct Agent initialized with {len(available_agents)} available A2A agents: {available_agents}")
        print("🧠 Using Anthropic Claude as the reasoning engine")
        print(f"📡 HTTP endpoint available at: http://localhost:{HTTP_SERVER_PORT}{FLIGHTS_ENDPOINT_PATH}")
    
    async def process_external_message(self, external_msg: InternalMessage, thread_id: str | None = None) -> str:
        """Process an external message and add it to agent memory."""
        if not self.agent_graph:
            return "❌ Agent not initialized. Please run initialize() first."
        
        try:
            thread_id = thread_id if thread_id else (external_msg.thread_id or f"external_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            print("\n🔍 External message\n")
            print("-" * 60)
            
            config = {"configurable": {"thread_id": thread_id}}
            user_message = json.dumps(external_msg.user_input, indent=2)
            messages = [("user", f"Source: {external_msg.source}\nResults: {user_message}")]
            
            print("🤖 Processing external message...")
            last_message = ""
            async for chunk in self.agent_graph.astream(
                {"messages": messages},
                config=config
            ):
                print(chunk)
                last_message = chunk
            
            if isinstance(last_message, dict):
                for chunk_type, chunk_data in last_message.items():
                    if isinstance(chunk_data, dict) and 'messages' in chunk_data:
                        for message in chunk_data['messages']:
                            if hasattr(message, 'content'):
                                print(f"\n**** 🤖 Agent Response to External Message pretty print *****\n{message.content}\n" + "*" * 61)
                                break
            
            return last_message if last_message else "External message processed successfully."
            
        except Exception as e:
            error_msg = f"❌ Error processing external message: {str(e)}"
            print(error_msg)
            return error_msg
    
    async def chat(self, user_input: str, thread_id: str = "default") -> str:
        """Process user input and return response."""
        if not self.agent_graph:
            return "❌ Agent not initialized. Please run initialize() first."
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            messages = [("user", user_input)]
            
            last_message = ""
            async for chunk in self.agent_graph.astream(
                {"messages": messages},
                config=config
            ):
                print(chunk)
                last_message = chunk
            
            return last_message if last_message else "Response completed - check the output above."
            
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"


def run_http_server(agent: ReactChatAgent):
    """Run the HTTP server in a separate thread."""
    uvicorn.run(
        agent.app, 
        host="0.0.0.0", 
        port=HTTP_SERVER_PORT,
        log_level="warning"
    )

async def main():
    """Main CLI loop for the chat agent with HTTP endpoint integration."""
    print("🚀 Starting LangGraph ReAct Chat Agent with A2A Integration")
    print("🧠 Powered by Anthropic Claude")
    print("📡 HTTP API Server Enabled")
    print("=" * 60)
    
    logging.basicConfig(level=logging.WARNING)
    
    async with httpx.AsyncClient() as httpx_client:
        agent = ReactChatAgent()
        await agent.initialize(httpx_client)
        
        print(f"🌐 Starting HTTP server on port {HTTP_SERVER_PORT}...")
        http_thread = threading.Thread(target=run_http_server, args=(agent,))
        http_thread.daemon = True
        http_thread.start()
        
        print("\n💬 Chat Agent Ready! (Type 'quit' to exit)")
        print("You can ask about:")
        print("  - Airport knowledge base: 'find airports in Madrid'")
        print("  - Airport information: 'what airports are in Tokyo'") 
        print("  - Employee flight requests: 'check pending flight requests'")
        print("  - Employee status: 'check John Smith flight request'")
        print("  - Flight search: 'search flights from AEP on 2025-11-20'")
        print("  - Real-time flights: 'find flights from JFK to LAX on 2025-12-01'")
        print("\n📡 HTTP Endpoints available:")
        print(f"  - POST http://localhost:{HTTP_SERVER_PORT}{FLIGHTS_ENDPOINT_PATH}")
        print(f"  - GET  http://localhost:{HTTP_SERVER_PORT}/api/status")
        print("-" * 60)
        
        thread_id = "console_session_" + str(uuid4())[:8]
        prompt_shown = False
        should_exit = False
        
        while not should_exit:
            try:
                while not agent.external_message_queue.empty():
                    external_msg = agent.external_message_queue.get()
                    await agent.process_external_message(external_msg)
                    prompt_shown = False
                
                if not prompt_shown:
                    print("\n👤 You: ", end="", flush=True)
                    prompt_shown = True
                
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    user_input = input().strip()
                    prompt_shown = False
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_closed():
                                print("⚠️  Event loop is closed - cleaning up gracefully...")
                            else:
                                print("✅ Event loop is healthy")
                        except RuntimeError:
                            print("ℹ️  No event loop available in current context")
                        
                        print("👋 Goodbye!")
                        should_exit = True
                    
                    if user_input:
                        print("🤖 LLM: ...", end="\n", flush=True)
                        response = await agent.chat(user_input, thread_id)
                        
                        if isinstance(response, dict):
                            for chunk_type, chunk_data in response.items():
                                if isinstance(chunk_data, dict) and 'messages' in chunk_data:
                                    for message in chunk_data['messages']:
                                        if hasattr(message, 'content'):
                                            print(f"\n**** 🤖 Agent pretty print *****\n{message.content}\n" + "*" * 31)
                                            break
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                should_exit = True
            except Exception as e:
                if "Event loop is closed" in str(e) or "RuntimeError" in str(type(e).__name__):
                    print(f"\n⚠️  Event loop issue detected: {e}")
                    print("ℹ️  This is usually safe to ignore during shutdown")
                else:
                    print(f"\n❌ Error: {e}")

        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
