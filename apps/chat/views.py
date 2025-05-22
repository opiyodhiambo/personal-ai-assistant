from datetime import datetime
import json
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.chat.clients.whatsapp_client import WhatsAppClient
from apps.chat.config import WhatsAppConfig
from apps.llm.clients.ollama_client import OllamaClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class WhatsAppWebhookView(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.whatsapp = WhatsAppClient()
        self.ollama = OllamaClient()
        self.config = WhatsAppConfig()

    
    def post(self, request):
        try:

            # We prepare our prompt
            message = request.data['entry'][0]['changes'][0]['value']['messages'][0]
            sender = message['from']
            timestamp = message['timestamp']
            prompt = message['text']['body']

            # ask our LLM
            start_time = datetime.now()
            print(f"start_time {start_time}")

            full_reply = self.ollama.ask(prompt)
            end_time = datetime.now()
            print(f"\n{full_reply}\nPrompt ended at {end_time}")

            duration = (end_time - start_time).total_seconds()
            print(f"This prompt took {duration} seconds")
            
            self.whatsapp.send_message(to=sender, text=full_reply)
            return Response({"status": "sent"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == self.config.verify_token:
            return Response({'hub.challenge': challenge})
        return Response({}, status=status.HTTP_403_FORBIDDEN)