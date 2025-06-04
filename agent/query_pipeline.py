from langchain_ollama import ChatOllama
from agent.service.calendar import GoogleCalendar
from agent.embedding.embedder import EmbeddingModel
from agent.models import UserIntent
from agent.service.intents import IntentDetector
from agent.prompt_engineering.prompt_optimizer import PromptOptimizer
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
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


    async def run(self, user_query: str, session_id: str):
        """
        Entry point for handling user queries. It detects intent and dispatches accordingly.
        """
        print(f"Running query pipeline")

        # First, we classify the user intent (create event, check calendar, or general query)
        user_intent = self.intent_detector.classify(user_query)
        
        # Route the query to the appropriate handler based on detected intent
        if user_intent == UserIntent.CREATE_EVENT:
            result = await self._handle_create_event(user_query=user_query, user_intent=user_intent, session_id=session_id)
            yield result

        elif user_intent == UserIntent.QUERY_CALENDAR:
            result = await self._handle_calendar_query(user_query=user_query, user_intent=user_intent, session_id=session_id)
            yield result

        elif user_intent == UserIntent.GENERAL:
            async for chunk in self._handle_general_query(user_query=user_query, user_intent=user_intent, session_id=session_id):
                yield chunk


    async def _handle_create_event(self, user_query: str, session_id: str, user_intent: UserIntent):
        """
        Extracts event data from the query and creates a calendar entry.
        If successful, it passes the event back to the LLM for a confirmation message.
        """
        event_data = self.intent_detector.extract_event(user_query)

        # We verify whether the model could extract a start_time.
        if not event_data.get("start_time"):
            return "⚠️ I couldn't understand when to schedule the event. Please specify a clear time."

        # Push the event to Google Calendar
        added_event = self.calendar.add_event(event_data)

        # Let the LLM generate a confirmation or summary
        return await self.call_llm(user_query, context=added_event, user_intent=user_intent, session_id=session_id)


    async def _handle_calendar_query(self, user_query: str, session_id: str, user_intent: UserIntent):
        """
        Fetches upcoming events from the calendar and provides them to the LLM for summarization.
        """
        events = self.calendar.get_upcoming_events()
        return await self.call_llm(user_query, context=events, user_intent=user_intent, session_id=session_id)


    async def _handle_general_query(self, user_query: str, session_id: str, user_intent: UserIntent):
        """
        Handles open-ended queries by retrieving contextually similar documents or embeddings.
        """
        context = self.embedder.retrieve_context(user_query)
        async for chunk in self.stream_llm(user_query, context=context, user_intent=user_intent, session_id=session_id):
            yield chunk

        
    # For normal use (no streaming)
    async def call_llm(self, user_query: str, context: str, session_id: str, user_intent: UserIntent):

        """
        Sends the processed query to the LLM. Memory-aware behavior is handled automatically
        via RunnableWithMessageHistory and ConversationSummaryMemory.
        """
        optimized_prompt = self.prompt_optimizer.build(user_query, context, user_intent)
        response =  await self.memory_chain.ainvoke(
            {"input": optimized_prompt},
            config={"configurable": {"session_id": session_id}}
        )
        print(f"response {response}")
        return response.content


    # For streaming use cases only
    async def stream_llm(self, user_query: str, context: str, session_id: str, user_intent: UserIntent):
        optimized_prompt = self.prompt_optimizer.build(user_query, context, user_intent)
        print(f"optimized_prompt {optimized_prompt}")
        async for chunk in self.memory_chain.astream(
            {"input": optimized_prompt},
            config={"configurable": {"session_id": session_id}}
        ):
            print(f"chunk {chunk}")
            yield chunk.content



    def _get_memory(self, session_id: str) -> BaseChatMessageHistory:
        """
        Returns a memory object for the session. If one doesn't exist yet, it creates it.
        We use ChatMessageHistory for summarizing long conversations into context-efficient summaries.
        """
        if session_id not in self.memory_store:
            self.memory_store[session_id] = ChatMessageHistory()
        return self.memory_store[session_id]
