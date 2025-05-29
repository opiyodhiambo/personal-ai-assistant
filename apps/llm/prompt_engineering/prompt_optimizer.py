from apps.llm.models import UserIntent


class PromptOptimizer:
    def __init__(self, template_dir: str = "templates", template_name: str = "personal_assistant_prompt.j2"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template(template_name)

    def build(self, user_query, context, user_intent: UserIntent):
        pass