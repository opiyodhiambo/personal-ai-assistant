from apps.llm.clients.ollama_client import OllamaClient
from apps.llm.embedding.embedder import EmbeddingModel
from apps.llm.prompt_engineering.prompt_optimizer import PromptOptimizer

class QueryPipeline:
    def __init__(self):
        self.embedder = EmbeddingModel()
        self.prompt_optimizer = PromptOptimizer()
        self.llm = OllamaClient()

    def run(self, user_query):
        context = self.embedder.retrieve_context(user_query)
        optimized_prompt = self.prompt_optimizer.build(user_query, context)
        response = self.llm.ask(prompt=optimized_prompt)
        return response
