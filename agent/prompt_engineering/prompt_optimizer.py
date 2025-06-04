import os
from jinja2  import Environment, FileSystemLoader, TemplateNotFound
from agent.models import UserIntent


class PromptOptimizer:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(base_dir, "prompts")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        # Mapping of user intents to corresponding template filenames
        self.template_map = {
            UserIntent.CREATE_EVENT: "create_event_prompt.j2",
            UserIntent.QUERY_CALENDAR: "query_calendar_prompt.j2",
            UserIntent.GENERAL: "general_prompt.j2"
        }


    def build(self, user_query, context, user_intent: UserIntent):
        """
        Renders the appropriate prompt template ysing the user query, context and intent
        """
        template_name = self.template_map.get(user_intent)

        if not template_name:
            raise ValueError(f"No template defined for intent: {user_intent}")
        
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_name}' not found in '{self.env.loader.searchpath}'")

        return template.render({
            "query": user_query.strip(),
            "context": context.strip() if context else "No relevant context found"
        })