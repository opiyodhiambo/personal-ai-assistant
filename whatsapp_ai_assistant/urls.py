from django.contrib import admin
from django.urls import path
from apps.chat.views import WhatsAppWebhookView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("webhook/", WhatsAppWebhookView.as_view(), name="whatsapp_webhook")
]
