from datetime import datetime
import json
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.chat.clients.whatsapp_client import WhatsAppClient
from apps.chat.config import WhatsAppConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class WhatsAppWebhookView(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.whatsapp = WhatsAppClient()
        self.config = WhatsAppConfig()

    
    def post(self, request):
        pass


    def get(self, request):
        pass