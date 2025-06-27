"""
A2A Agent for Flight Search functionality with Push Notification capabilities.
"""
import httpx
import uvicorn
from uuid import uuid4

from a2a.server.apps import A2AStarletteApplication
from custom_request_handler import CustomRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Task,
    TaskStatus,
    TaskState,
)
from agent_executor import (
    FlightSearchAgentExecutor,
)

if __name__ == '__main__':

    flight_search_skill = AgentSkill(
        id='flight_search',
        name='Flight Search',
        description='Search for flights by airport IATA code and departure date using real-time aviation data',
        tags=['flight', 'search', 'departure', 'aviation', 'real-time', 'schedule'],
        examples=[
            'search flights from AEP on 2025-11-02',
            'find departures from JFK on 2025-12-15',
            'get flights leaving LAX tomorrow',
            'search flights from LHR on 2025-10-25',
            'find departures from CDG on specific date'
        ],
    )

    public_agent_card = AgentCard(
        name='Flight Search Agent',
        description='Real-time flight search agent with push notification capabilities for aviation data',
        url='http://localhost:9993/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
        skills=[flight_search_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    task = Task(
        id=str(uuid4()),
        contextId=str(uuid4()),
        status=TaskStatus(
            state=TaskState.submitted,
        )
    )

    request_handler = CustomRequestHandler(
        agent_executor=FlightSearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client=httpx.AsyncClient())
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9993) 