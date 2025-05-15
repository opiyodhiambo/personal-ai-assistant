import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppConfig:
    def __init__(self):
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.verify_token = os.getenv("VERIFY_TOKEN")
        self.graph_api_version = os.getenv("GRAPH_API_VERSION")

    @property
    def api_url(self):
        return f"https://graph.facebook.com/{self.graph_api_version}/{self.phone_number_id}/messages"
