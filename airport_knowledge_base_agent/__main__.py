"""
A2A Agent with Airport Knowledge Base functionality.
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
    AirportKnowledgeBaseAgentExecutor,
)

if __name__ == '__main__':

    airport_knowledge_skill = AgentSkill(
        id='airport_knowledge_base',
        name='Airport Knowledge Base',
        description='Retrieve correct airport names and find airports in specific cities from knowledge base',
        tags=['airport', 'knowledge', 'lookup', 'city', 'information'],
        examples=[
            'get airports in Madrid',
            'find correct name for Tokyo airport', 
            'airports in New York City',
            'Barcelona airport information',
            'what airports are in London'
        ],
    )

    public_agent_card = AgentCard(
        name='Airport Knowledge Base Agent',
        description='Knowledge base agent for retrieving correct airport names and city-airport mappings',
        url='http://localhost:9991/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[airport_knowledge_skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=AirportKnowledgeBaseAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9991)
