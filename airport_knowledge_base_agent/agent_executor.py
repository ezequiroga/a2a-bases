"""
This file contains the AirportKnowledgeBaseAgent class, used as a knowledge base for airport information and city-airport mappings.
"""
import os
import uuid
from fuzzywuzzy import fuzz, process
import pandas as pd
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task
from a2a.types import Part, TextPart, TaskState, Task, Message, Role

class AirportKnowledgeBaseAgent:
    """Agent that serves as a knowledge base for airport information, providing correct airport names and city-airport mappings."""

    def __init__(self):
        """Initialize the agent and load airport knowledge base."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        airports_csv_path = os.path.join(base_dir, 'databases', 'airport-codes.csv')
        countries_csv_path = os.path.join(base_dir, 'databases', 'isocountry-codes.csv')
        
        try:
            df_airports = pd.read_csv(airports_csv_path)
            df_countries = pd.read_csv(countries_csv_path)
            
            self.country_dict = dict(zip(df_countries['Code'], df_countries['Name']))
            
            df_valid = df_airports.dropna(subset=['name', 'municipality'])
            
            self.airport_knowledge = df_valid[df_valid['type'].str.contains('airport', case=False, na=False)]

            self.airport_knowledge = self.airport_knowledge[self.airport_knowledge['iata_code'].notna()]
            
            self.airport_names = self.airport_knowledge['name'].tolist()
            self.municipalities = self.airport_knowledge['municipality'].tolist()
            
            print(f"\n✅ Loaded airport knowledge base: {len(self.airport_knowledge)} airports from {self.airport_knowledge['iso_country'].nunique()} countries\n")
            
        except Exception as e:
            print(f"❌ Error loading airport knowledge base: {str(e)}")
            self.country_dict = {}
            self.airport_knowledge = pd.DataFrame()
            self.airport_names = []
            self.municipalities = []

    async def invoke(self, task: Task, updater: TaskUpdater, query: str = None) -> None:
        """
        Retrieve airport information using fuzzy matching by name and municipality.
        
        Args:
            context: Request context
            event_queue: Event queue for streaming messages
            query: Search string (city or airport name)
            
        Returns:
            String with top 5 airport names and top 5 cities with their airports
        """
        if self.airport_knowledge.empty:
            return "Airport knowledge base not loaded. Please check the database files."
        
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                "📚 Accessing airport knowledge base...",
                task.contextId,
                task.id,
            ),
        )
        
        try:
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "🛫 Looking up airport names...",
                    task.contextId,
                    task.id,
                ),
            )
            
            airport_matches = process.extract(query, self.airport_names, limit=5, scorer=fuzz.partial_ratio)
            
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "🏙️ Looking up city airports...",
                    task.contextId,
                    task.id,
                ),
            )
            
            municipality_matches = process.extract(query, self.municipalities, limit=5, scorer=fuzz.partial_ratio)
            
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "📊 Processing results...",
                    task.contextId,
                    task.id,
                ),
            )
            
            result_lines = ""
            
            result_lines += "🛫 TOP 5 AIRPORT NAMES:\n"
            for match_name, score in airport_matches:
                airport_info = self.airport_knowledge[self.airport_knowledge['name'] == match_name].iloc[0]
                country_name = self.country_dict.get(airport_info['iso_country'], airport_info['iso_country'])
                result_lines += f"  • {match_name} ({score}% match)\n"
                result_lines += f"    📍 {airport_info['municipality']}, {country_name}\n"
                if pd.notna(airport_info['iata_code']):
                    result_lines += f"    ✈️ IATA: {airport_info['iata_code']}\n"
                result_lines += "\n"
            
            result_lines += "🏙️ TOP 5 CITIES:\n"
            processed_municipality_country = set()
            city_results = []
            
            for match_municipality, score in municipality_matches:
                city_airports = self.airport_knowledge[self.airport_knowledge['municipality'] == match_municipality]
                
                for country_code in city_airports['iso_country'].unique():
                    municipality_country_key = f"{match_municipality}_{country_code}"
                    if municipality_country_key not in processed_municipality_country:
                        processed_municipality_country.add(municipality_country_key)
                        country_airports = city_airports[city_airports['iso_country'] == country_code]
                        country_name = self.country_dict.get(country_code, country_code)
                        
                        city_results.append({
                            'municipality': match_municipality,
                            'country': country_name,
                            'score': score,
                            'airports': country_airports
                        })
            
            for _, city_result in enumerate(city_results[:5]):
                result_lines += f"  • {city_result['municipality']}, {city_result['country']} ({city_result['score']}% match)\n"
                result_lines += "    ✈️ Airports:\n"
                
                airport_info = [(row['name'], row['iata_code']) for _, row in city_result['airports'].iterrows()]
                unique_airports = set(airport_info)
                for airport_name, iata_code in sorted(unique_airports):
                    result_lines += f"     - (IATA: {iata_code}) {airport_name}\n"
                result_lines += "\n"
            
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "✅ Knowledge base lookup completed!",
                    task.contextId,
                    task.id,
                ),
            )

            print(f"result_lines: {result_lines}")

            part = TextPart(text=result_lines)
            message = Message(
                role=Role.agent,
                parts=[part],
                messageId=str(uuid.uuid4()),
            )
            await updater.complete(message=message)

        except Exception as e:
            print(f"❌ Error occurred: {str(e)}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"❌ Error occurred: {str(e)}",
                    task.contextId,
                    task.id,
                ),
            )

class AirportKnowledgeBaseAgentExecutor(AgentExecutor):
    """Airport knowledge base agent executor."""

    def __init__(self):
        self.agent = AirportKnowledgeBaseAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)

        updater = TaskUpdater(event_queue, task.id, task.contextId)
        await self.agent.invoke(task, updater, query)

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        task = context.current_task
        if not task:
            task = new_task(context.message)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    "❌ Knowledge base lookup cancelled",
                    context.current_task.contextId,
                    context.current_task.id,
                ),
        )

