from django.db import models
from enum import Enum

class UserIntent(Enum):
    CREATE_EVENT = "create_event"
    QUERY_CALENDAR = "query_calendar" # we will give them events for that week
    GENERAL = "general"
