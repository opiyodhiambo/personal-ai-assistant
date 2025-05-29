from langchain_ollama import ChatOllama
from apps.llm.clients.google_calendar import GoogleCalendar
from apps.llm.embedding.embedder import EmbeddingModel
from apps.llm.models import UserIntent
from apps.llm.prompt_engineering.prompt_optimizer import PromptOptimizer
from apps.llm.service.intents import IntentDetector
from langchain.memory import ConversationSummaryMemory
from langchain.chains.conversation.base import ConversationChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

class QueryPipeline:
    def __init__(self):
        self.embedder = EmbeddingModel()
        self.prompt_optimizer = PromptOptimizer()
        self.intent_detector = IntentDetector()
        self.calendar = GoogleCalendar()
        
        # For a memory-aware chat
        self.memory_store = {}
        self.chat_llm = ChatOllama(model="llama3.2")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a personal assistant"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        self.memory_chain = RunnableWithMessageHistory(
            self.prompt | self.chat_llm,
            get_session_history=self._get_memory,
            input_messages_key="input",
            history_messages_key="history"

        )


    async def run(self, user_query: str):
        response = ""
        
        # Checking user intent
        user_intent = self.intent_detector.classify(user_query)
        
        if user_intent == UserIntent.CREATE_EVENT:
            return await self._handle_create_event(user_query=user_query)

        elif user_intent == UserIntent.QUERY_CALENDAR:
            return await self._handle_calendar_query(user_query=user_query)

        elif user_intent == UserIntent.GENERAL:
            context = self.embedder.retrieve_context(user_query)
            response += self.call_llm(user_query=user_query, context=context, user_intent=user_intent)

        return response
    

    async def _handle_create_event(self, user_query: str, stream: bool=False):
        event_data = self.intent_detector.extract_event(user_query)
        if not event_data.get("start_time"):
            return "⚠️ I couldn't understand when to schedule the event. Please specify a clear time."

        self.calendar.add_event(event_data)
        return await self.call_llm(user_query, context=event_data, user_intent=UserIntent.CREATE_EVENT, stream=stream)
    

    async def _handle_calendar_query(self, user_query: str, stream: bool=False):
        events = self.calendar.get_upcoming_events()
        return await self.call_llm(user_query, context=events, user_intent=UserIntent.QUERY_CALENDAR, stream=stream)
    

    async def _handle_general_query(self, user_query: str, stream: bool=False):
        context = self.embedder.retrieve_context(user_query)
        return await self.call_llm(user_query, context=context, user_intent=UserIntent.GENERAL, stream=stream)


    async def call_llm(self, user_query: str, context: str, session_id: str, user_intent: UserIntent, stream: bool):
        optimized_prompt = self.prompt_optimizer.build(user_query, context, user_intent)

        if stream:
            async for chunk in self.memory_chain.astream(
                {"input": optimized_prompt},
                config={"configurable": {"session_id": session_id}}
            ):
                yield chunk
        else:
            return await self.memory_chain.ainvoke(
                {"input": optimized_prompt},
                config={"configurable": {"session_id": session_id}}
            )
    

    def _get_memory(self, session_id: str):
        if session_id not in self.memory_store:
            self.memory_store[session_id] = ConversationSummaryMemory(
                llm=self.chat_llm,
                memory_key="history"
            )
        return self.memory_store[session_id]

    

    

