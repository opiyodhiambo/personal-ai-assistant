from django.db import models
from enum import Enum

class UserIntent(Enum):
    CREATE_EVENT = "create_event"
    QUERY_CALENDAR = "query_calendar"
    GENERAL = "general"
