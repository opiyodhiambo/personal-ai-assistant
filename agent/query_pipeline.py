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
        # Initialize all service dependencies
        self.embedder = EmbeddingModel()
        self.prompt_optimizer = PromptOptimizer()
        self.intent_detector = IntentDetector()
        self.calendar = GoogleCalendar()
        
        # This dictionary keeps per-session memory instances.
        # It allows us to persist conversational context across multiple turns using session IDs.
        self.memory_store = {}

        # We use a local LLM (Ollama-backed) to reduce latency and gain control over the model.
        self.chat_llm = ChatOllama(model="llama3.2")

        # Define the base prompt template. We include a system message,
        # a placeholder for chat history (managed by LangChain memory), and the user's message.
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a personal assistant"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # RunnableWithMessageHistory enables us to inject memory into our LLM chain.
        # We instantiate it only once here, since the prompt template remains static.
        # History is dynamically injected via _get_memory(), keeping the design clean.
        self.memory_chain = RunnableWithMessageHistory(
            self.prompt | self.chat_llm,
            get_session_history=self._get_memory,
            input_messages_key="input",
            history_messages_key="history"
        )


    async def run(self, user_query: str):
        """
        Entry point for handling user queries. It detects intent and dispatches accordingly.
        """
        response = ""

        # First, we classify the user intent (create event, check calendar, or general query)
        user_intent = self.intent_detector.classify(user_query)
        
        # Route the query to the appropriate handler based on detected intent
        if user_intent == UserIntent.CREATE_EVENT:
            return await self._handle_create_event(user_query=user_query)

        elif user_intent == UserIntent.QUERY_CALENDAR:
            return await self._handle_calendar_query(user_query=user_query)

        elif user_intent == UserIntent.GENERAL:
            # For general queries, retrieve context using our embedding model
            context = self.embedder.retrieve_context(user_query)
            response += self.call_llm(user_query=user_query, context=context, user_intent=user_intent)

        return response


    async def _handle_create_event(self, user_query: str, stream: bool = False):
        """
        Extracts event data from the query and creates a calendar entry.
        If successful, it passes the event back to the LLM for a confirmation message.
        """
        event_data = self.intent_detector.extract_event(user_query)

        # We verify whether the model could extract a start_time.
        if not event_data.get("start_time"):
            return "⚠️ I couldn't understand when to schedule the event. Please specify a clear time."

        # Push the event to Google Calendar
        self.calendar.add_event(event_data)

        # Let the LLM generate a confirmation or summary
        return await self.call_llm(user_query, context=event_data, user_intent=UserIntent.CREATE_EVENT, stream=stream)


    async def _handle_calendar_query(self, user_query: str, stream: bool = False):
        """
        Fetches upcoming events from the calendar and provides them to the LLM for summarization.
        """
        events = self.calendar.get_upcoming_events()
        return await self.call_llm(user_query, context=events, user_intent=UserIntent.QUERY_CALENDAR, stream=stream)


    async def _handle_general_query(self, user_query: str, stream: bool = False):
        """
        Handles open-ended queries by retrieving contextually similar documents or embeddings.
        """
        context = self.embedder.retrieve_context(user_query)
        return await self.call_llm(user_query, context=context, user_intent=UserIntent.GENERAL, stream=stream)


    async def call_llm(self, user_query: str, context: str, session_id: str, user_intent: UserIntent, stream: bool):
        """
        Sends the processed query to the LLM. Memory-aware behavior is handled automatically
        via RunnableWithMessageHistory and ConversationSummaryMemory.
        """
        # Build an optimized prompt using retrieved context and intent-aware formatting
        optimized_prompt = self.prompt_optimizer.build(user_query, context, user_intent)

        # If streaming is enabled, we yield each response chunk as it arrives.
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
        """
        Returns a memory object for the session. If one doesn't exist yet, it creates it.
        We use ConversationSummaryMemory for summarizing long conversations into context-efficient summaries.
        """
        if session_id not in self.memory_store:
            self.memory_store[session_id] = ConversationSummaryMemory(
                llm=self.chat_llm,
                memory_key="history"
            )
        return self.memory_store[session_id]
