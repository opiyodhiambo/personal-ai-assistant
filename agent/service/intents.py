import os 
import json
from typing import Tuple
import ollama
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from agent.models import EventCreate, UserIntent


class IntentDetector:
    """
    Detects user intent from natural language queries and extracts structured data
    to support calendar event creation and retrieval.

    - Uses simple rule-based logic as a fast first-pass classifier.
    - Falls back to an LLM (via Ollama) for ambiguous or low-confidence cases.
    - Also supports structured event extraction using a Jinja2-driven prompt.
    """

    def __init__(self, threshold: float = 0.7):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(base_dir, "../prompt_engineering/prompts")
        self.threshhold = threshold
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.classification_model = "llama3.2"  # Ollama model to use


    def classify(self, user_query: str) -> UserIntent:
        
        """
        Classifies the intent of a user query (e.g. create event, check calendar).
        Uses rule-based classification first, then falls back to LLM if confidence is low.
        """
    
        intent = self._llm_fallback_classify(user_query)
        print(f"Handling user_query {user_query} with intent {intent}")
        return intent


    def extract_event(self, user_query: str) -> EventCreate:
        """
        Extracts structured event information from the user's natural language query
        using a prompt template and Ollama for LLM-based parsing.

        Returns:
            EventCreate: a structured Pydantic model instance containing event details.

        Raises:
            ValueError: if the LLM response is not a valid JSON or can't be parsed.
        """

        prompt_template = self.jinja_env.get_template("event_extraction_prompt.j2")
        prompt = prompt_template.render(query=user_query)

        try:
            response = ollama.chat(
                model=self.classification_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0}  # Setting temperature to 0 for deterministic output
            )
            content = response['message']['content'].strip()
            event_dict = json.loads(content)  # Parse LLM output as JSON

            for field in ["summary", "start_time", "end_time"]:
                if field not in event_dict:
                    raise ValueError(f"Missing required field: '{field}' in model response.")
                
            return EventCreate(**event_dict)
        
        except json.JSONDecodeError:
            print(f"[IntentDetector] Failed to parse JSON: {content}")
            raise ValueError("LLM did not return valid JSON.")
        except ValidationError as ve:
            print(f"[IntentDetector] Validation error: {ve}")
            raise ValueError("Response JSON does not match expected EventCreate structure.")
        except Exception as e:
            print(f"[IntentDetector] Event extraction failed: {e}")
            raise ValueError("Could not extract event data")


    def __rule_based_classify(self, user_query: str) -> Tuple[UserIntent, float]:
        """
        A quick keyword-based heuristic classifier for common calendar intents.
        It outputs a confidence score to guide fallback decisions.

        Returns:
            Tuple[UserIntent, float]: Best-guess intent and associated confidence
        """
        query = user_query.lower()

        scores = {
            UserIntent.CREATE_EVENT: 0,
            UserIntent.QUERY_CALENDAR: 0,
            UserIntent.GENERAL: 0
        }

        # Simple heuristic: If query contains scheduling-related keywords
        if any(kw in query for kw in ["schedule", "create", "book"]):
            scores[UserIntent.CREATE_EVENT] += 0.7
        if "meeting" in query:
            scores[UserIntent.CREATE_EVENT] += 0.2

        if any(kw in query for kw in ["what's on", "do i have", "upcoming", "schedule"]):
            scores[UserIntent.QUERY_CALENDAR] += 0.7

        if any(kw not in query for kw in ["schedule", "create", "book", "what's on", "do i have", "upcoming", "schedule", "meeting"]):
            scores[UserIntent.GENERAL] += 0.8

        # Choose the intent with the highest score
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        if best_score == 0:
            return UserIntent.GENERAL, 0.0

        return best_intent, best_score


    def _llm_fallback_classify(self, user_query: str) -> UserIntent:
        """
        Uses an LLM (via Ollama) to classify intent when rule-based confidence is low.
        This relies on a well-crafted prompt template for consistent labels.
        """
        prompt_template = self.jinja_env.get_template("intent_prompt.j2")
        prompt = prompt_template.render(query=user_query)

        try:
            response = ollama.chat(
                model=self.classification_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0}
            )
            label = response['message']['content'].strip().lower()

            # Mapping the raw label to our enum type
            mapping = {
                "create_event": UserIntent.CREATE_EVENT,
                "check_calendar": UserIntent.QUERY_CALENDAR
            }
            return mapping.get(label, UserIntent.GENERAL)
        except Exception as e:
            print(f"[IntentDetector] Ollama error: {e}")
            return UserIntent.GENERAL
