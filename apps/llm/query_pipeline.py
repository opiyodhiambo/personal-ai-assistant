from apps.llm.clients.google_calendar import GoogleCalendar
from apps.llm.clients.ollama_client import OllamaClient
from apps.llm.embedding.embedder import EmbeddingModel
from apps.llm.models import UserIntent
from apps.llm.prompt_engineering.prompt_optimizer import PromptOptimizer
from apps.llm.service.intents import IntentDetector

class QueryPipeline:
    def __init__(self):
        self.embedder = EmbeddingModel()
        self.prompt_optimizer = PromptOptimizer()
        self.llm = OllamaClient()
        self.intent_detector = IntentDetector()
        self.calendar = GoogleCalendar()

    def run(self, user_query):
        response = ""
        
        # Checking user intent
        user_intent = self.intent_detector.classify(user_query)
        
        if user_intent == UserIntent.CREATE_EVENT:
            event_data = self.intent_detector.extract_event(user_query)
            self.calendar.add_event(event_data)
            response += self.call_llm(user_query=user_query, context=event_data, user_intent=user_intent)

        elif user_intent == UserIntent.QUERY_CALENDAR:
            upcoming_events = self.calendar.get_upcoming_events()
            response += self.call_llm(user_query=user_query, context=upcoming_events, user_intent=user_intent)

        elif user_intent == UserIntent.GENERAL:
            context = self.embedder.retrieve_context(user_query)
            response += self.call_llm(user_query=user_query, context=context, user_intent=user_intent)

        return response
    

    def call_llm(self, user_query, context, user_intent) -> str:
        optimized_prompt = self.prompt_optimizer.build(user_query, context, user_intent)
        return self.llm.ask(optimized_prompt)

    

    

