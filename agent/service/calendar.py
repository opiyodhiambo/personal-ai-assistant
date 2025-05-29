from agent.models import EventCreate, UpcomingEventsResponse


class GoogleCalendar:
    def __init__(self):
        # auth and setup here if needed
        pass

    def add_event(self, event_data: EventCreate) -> str:
        """
        Adds an event to Google Calendar and returns the event ID or URL.
        """
        pass

    def get_upcoming_events(self, max_results: int = 10) -> UpcomingEventsResponse:
        """
        Fetches upcoming events and returns a structured summary.
        """
        pass
