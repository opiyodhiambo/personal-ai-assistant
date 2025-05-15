import logging
import requests
from apps.chat.config import WhatsAppConfig


class WhatsAppClient:
    def __init__(self):
        self.config = WhatsAppConfig()
        self.headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json',
        }


    def send_message(self, to, text):
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": text}
        }
        response = requests.post(self.config.api_url, headers=self.headers, json=payload)
        self.log_http_response(response)
        return response.json()
    

    def log_http_response(self, response):
        logging.info(f"Status: {response.status_code}")
        logging.info(f"Content-type: {response.headers.get('content-type')}")
        logging.info(f"Body: {response.text}")
    

    


