# A2A Multi-Agent Flight Management System

A comprehensive multi-agent system built with the A2A (Agent-to-Agent) protocol that provides intelligent flight search, airport knowledge base, and employee flight request management capabilities.
The system combines multiple specialized agents with a centralized chat interface powered by LangGraph and Anthropic Claude.

## 🏗️ System Architecture

The system consists of **4 main components**:

1. **Chat Agent** - Central conversational interface using LangGraph + Claude 3.5 Sonnet
2. **Employee Flight Request Agent** - Employee flight booking management system
3. **Airport Knowledge Base Agent** - Airport information and city-airport mapping service
4. **Flight Search Agent** - Real-time flight search using Aviation Stack API

All agents communicate via the A2A protocol, enabling seamless inter-agent collaboration and streaming responses.

## 🤖 Agent Details

### 1. Chat Agent (`chat_agent.py`)

- **Purpose**: Central conversational interface that orchestrates other agents
- **Technology**: LangGraph ReAct pattern with Anthropic Claude 3.5 Sonnet
- **Features**:
  - Natural language processing and routing
  - Real-time streaming responses
  - HTTP endpoint for receiving push notifications
  - Memory persistence across conversations
  - Asynchronous background task execution

#### Sub-component: Agent Registry

- **Purpose**: Central system for registering and discovering available agents
- **Implementation**: Integrated within the chat agent for simplicity (ideally should be an independent system)
- **Capabilities**:
  - Automatic registration of available A2A agents
  - Port and endpoint mapping for each agent
  - Agent status and availability verification
  - Agent capability information retrieval
  - Inter-agent connection management

### 2. Employee Flight Request Agent

- **Location**: [`employee_flight_request_agent/`](./employee_flight_request_agent/)
- **Purpose**: Manage employee flight requests and booking status
- **Capabilities**:
  - Check pending flight requests
  - Review booked flights
  - Employee-specific query handling
  - Request status tracking

### 3. Airport Knowledge Base Agent

- **Location**: [`airport_knowledge_base_agent/`](./airport_knowledge_base_agent/)
- **Purpose**: Provides airport information and city-airport mappings
- **Data Sources**: Local CSV databases that simulate real databases (airport-codes.csv, isocountry-codes.csv)
- **Capabilities**:
  - Fuzzy search for airport names
  - City-to-airports mapping
  - IATA code lookup
  - Country-specific airport filtering

### 4. Flight Search Agent

- **Location**: [`flight_search_agent/`](./flight_search_agent/)
- **Purpose**: Real-time flight search using external aviation data
- **API**: Aviation Stack API integration
- **Features**:
  - Scheduled flight searches by IATA code and date
  - Push notification support for background searches
  - ReAct agent pattern with intelligent query processing
  - Comprehensive flight details (airlines, schedules, aircraft, terminals)

## 🚀 Getting Started

### Prerequisites

1. **Python 3.8+** and **uv** package manager
2. **Environment Variables**:

   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key
   AVIATION_STACK_API_KEY=your_aviation_stack_api_key
   ```

3. **Dependencies**: Install via `uv` or `pip install -r requirements.txt`

> **IMPORTANT NOTE**: The A2A protocol library must be installed using **UV** to avoid installation errors. This is the recommended approach according to the official A2A documentation. Using pip may result in dependency conflicts or incomplete installations.

### Installation

1. Clone the repository and navigate to `dev_post/`
2. Copy the environment template and add your API keys:

   ```bash
   cp env_template .env
   # Edit .env file with your actual API keys
   ```

3. Install dependencies in each agent directory

### Running the System

#### 1. Start Individual A2A Agents

Each agent runs on a different port and must be started separately:

**Employee Flight Request Agent** (Port 9992):

```bash
cd employee_flight_request_agent/
uv run . --host 0.0.0.0
```

**Airport Knowledge Base Agent** (Port 9991):

```bash
cd airport_knowledge_base_agent/
uv run . --host 0.0.0.0
```

**Flight Search Agent** (Port 9993):

```bash
cd flight_search_agent/
uv run . --host 0.0.0.0
```

#### 2. Start the Chat Interface

```bash
python3 chat_agent.py
```

The chat agent will:

- Initialize connections to all A2A agents
- Start HTTP server on port 9990 for push notifications
- Launch the interactive chat interface

## 💬 Using the Chat Interface

Once all agents are running, you can interact with the system using natural language:

### Example Queries

**Employee Flight Requests:**

```text
check pending flight requests
check John Smith flight request
show booked flights
```

**Airport Information:**

```text
find airports in Madrid
what airports are in Tokyo
Barcelona airport information
```

**Flight Search:**

```text
search flights from AEP on 2025-11-20
find departures from JFK on 2025-12-15
get flights leaving LAX tomorrow
```

### Chat Commands

- Type your query naturally
- Use `quit` or `exit` to stop the chat
- The system provides real-time streaming responses
- Background flight searches send push notifications when completed

## 🔧 Technical Features

### A2A Protocol Integration

- **Streaming Communication**: Real-time message streaming between agents
- **Push Notifications**: Background task completion notifications
- **Task Management**: Persistent task tracking and status updates
- **Error Handling**: Graceful degradation when agents are unavailable

### LangGraph ReAct Pattern

- **Tool Integration**: Seamless tool calling for each specialized agent
- **Memory Management**: Conversation persistence across sessions
- **Intelligent Routing**: Automatic agent selection based on query content
- **Response Streaming**: Real-time response generation and display

### Asynchronous Architecture

- **Event Loop Management**: Proper asyncio handling for background tasks
- **Concurrent Operations**: Multiple agent calls without blocking
- **HTTP Server Integration**: FastAPI server for external notifications
- **Thread Safety**: Safe concurrent access to shared resources

## 📁 Project Structure

```text
dev_post/
├── chat_agent.py                          # Main chat interface
├── databases/                             # Airport and country data
│   ├── airport-codes.csv
│   └── isocountry-codes.csv
├── employee_flight_request_agent/         # Employee request agent
│   ├── __main__.py
│   └── agent_executor.py
├── airport_knowledge_base_agent/          # Airport knowledge agent
│   ├── __main__.py
│   ├── agent_executor.py
│   └── test_airport_knowledge_base.py
├── flight_search_agent/                   # Flight search agent
│   ├── __main__.py
│   ├── agent_executor.py
│   └── custom_request_handler.py
├── tests/                                 # Test files
│   ├── test_airport_knowledge_base.py
│   ├── test_employee_flight_request.py
│   ├── test_flight_search.py
│   └── test_flights_endpoint.py
└── README.md
```

## 🔌 API Endpoints

### Chat Agent HTTP Endpoints

- `POST /api/flights-findings` - Receive flight search results
- `GET /api/status` - System status and agent availability

### A2A Agent Endpoints

According to the A2A protocol, each agent exposes their capabilities card at:

- `GET /.well-known/agent.json` - Agent capability discovery

## 🧪 Testing

Test individual components:

```bash
# Run tests as Python modules from dev_post/ directory

# Test employee flight requests
python -m tests.test_employee_flight_request

# Test airport knowledge base
python -m tests.test_airport_knowledge_base

# Test flight search
python -m tests.test_flight_search

# Test HTTP endpoints
python -m tests.test_flights_endpoint
```

## 🎯 Key Capabilities

✅ **Multi-Agent Coordination**: Seamless communication between specialized agents  
✅ **Natural Language Interface**: Conversational interaction with complex backend systems  
✅ **Real-Time Streaming**: Live response generation and display  
✅ **Background Processing**: Non-blocking flight searches with push notifications  
✅ **Data Integration**: Airport databases and external aviation APIs  
✅ **Error Resilience**: Graceful handling of agent unavailability  
✅ **Memory Persistence**: Conversation context across multiple interactions  
✅ **Extensible Architecture**: Easy addition of new agents and capabilities  

## 📝 Notes

- The system automatically detects available agents on startup
- Flight searches run in the background and send results via push notifications
- Each agent can be developed and deployed independently
- The chat interface provides detailed logging of all agent interactions
- All agents support both streaming and non-streaming communication modes

## 📊 Data Sources

The CSV databases used in the Airport Knowledge Base Agent were downloaded from:

- **Country codes**: [DataHub - Country List](https://datahub.io/core/country-list)
- **Airport codes**: [DataHub - Airport Codes](https://datahub.io/core/airport-codes)
