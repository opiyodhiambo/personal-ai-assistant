from django.db import models
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserIntent(Enum):
    CREATE_EVENT = "create_event"
    QUERY_CALENDAR = "query_calendar" # we will give them events for that week
    GENERAL = "general"


class EventCreate(BaseModel):
    summary: str = Field(..., description="Title of the event")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    start_time: datetime = Field(..., description="Start time in ISO 8601 format")
    end_time: datetime = Field(..., description="End time in ISO 8601 format")
    time_zone: Optional[str] = Field("UTC", description="Time zone for the event, defaults to UTC")
    attendees_emails: Optional[list[str]] = Field(default_factory=list, description="List of attendee emails")


class EventSummary(BaseModel):
    summary: str
    start_time: datetime
    end_time: datetime
    organizer_name: Optional[str] = None
    location: Optional[str] = None
    html_link: Optional[str] = None


class UpcomingEventsResponse(BaseModel):
    events: list[EventSummary]


