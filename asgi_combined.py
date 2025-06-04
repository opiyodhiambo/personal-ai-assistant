# asgi_combined.py
import os
from django.core.asgi import get_asgi_application
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount
from starlette.applications import Starlette

from ai_assistant.chat_interface.main import app as fastapi_app

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_assistant.settings")

# Django ASGI app
django_asgi_app = get_asgi_application()

# Mount static directory properly
current_dir = os.path.dirname(__file__)
static_path = os.path.join(current_dir, "ai_assistant", "chat_interface", "static")
fastapi_app.mount("/static", StaticFiles(directory=static_path), name="static")

# Starlette app to combine both
routes = [
    Mount("/fastapi", app=fastapi_app),  # FastAPI at /fastapi/*
    Mount("/", app=django_asgi_app),     # Django at root
]

application = Starlette(routes=routes)
