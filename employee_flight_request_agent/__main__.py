"""
A2A Agent for Employee Flight Request Management and Status Checking.
"""
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import (
    EmployeeFlightRequestAgentExecutor,
)

if __name__ == '__main__':

    list_pending_requests_skill = AgentSkill(
        id='list_pending_requests',
        name='List Pending Flight Requests',
        description='List all employee flight requests that are not yet booked',
        tags=['flight', 'requests', 'pending', 'left', 'available', 'not booked', 'employee'],
        examples=[
            'list pending flight requests',
            'show pending requests',
            'which flights are not booked',
            'display remaining requests'
        ],
    )

    list_booked_requests_skill = AgentSkill(
        id='list_booked_requests',
        name='List Booked Flight Requests',
        description='List all employee flight requests that have been booked with flight details',
        tags=['flight', 'requests', 'booked', 'taken', 'purchased', 'confirmed'],
        examples=[
            'show booked flight requests',
            'list booked requests',
            'which flights are confirmed',
            'booked flights'
        ],
    )

    check_employee_request_skill = AgentSkill(
        id='check_employee_request',
        name='Check Employee Flight Request Status',
        description='Check the flight request status for a specific employee by name',
        tags=['flight', 'request', 'status', 'employee', 'check'],
        examples=[
            'check John Smith flight request',
            'flight status for Maria Garcia',
            'does Robert Johnson have a flight request',
            'Anna Thompson flight information'
        ],
    )

    public_agent_card = AgentCard(
        name='Employee Flight Request Management Agent',
        description='Agent for managing and checking employee flight requests and bookings',
        url='http://localhost:9992/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            list_pending_requests_skill,
            list_booked_requests_skill,
            check_employee_request_skill
        ],
        supportsAuthenticatedExtendedCard=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=EmployeeFlightRequestAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9992) 