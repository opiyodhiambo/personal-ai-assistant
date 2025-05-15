import logging
from ollama import chat

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model='llama3.2'):
        self.model = model

    
    def ask(self, prompt):
        try:
            print(f"\n{prompt}")
            stream = chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )

            full_reply = ""
            for chunk in stream:
                full_reply += chunk['message']['content']
            return full_reply

        except Exception as e:
            logging.exception("Error occurred while querying the LLM: {e}")
            return "Sorry, there was an error generating a response."

