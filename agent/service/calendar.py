from datetime import datetime, timedelta
import os
from agent.models import EventCreate, UpcomingEventsResponse, EventSummary
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendar:
    def __init__(self):
        creds = None
        if os.path.exists("token.json"): # We check if we haev a refresh token
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # We have the user log in when it does not exist
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request()) # Refresh the token if we can
            else: # If we can't, we go through the authorization flow
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # We then save the refresh token for subsequent requests
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        self.service = build('calendar', 'v3', credentials=creds)


        
    def add_event(self, event_data: EventCreate):
        """
        Adds an event to Google Calendar and returns the event ID or URL.
        """
        event = {
            'summary': event_data.summary,
            'location': event_data.location,
            'description': event_data.description,
            'start': {
                'dateTime': event_data.start_time.isoformat(),
                'timeZone': event_data.time_zone,
            },
            'end': {
                'dateTime': event_data.end_time.isoformat(),
                'timeZone': event_data.time_zone,
            },
            'attendees': [{'email': email} for email in event_data.attendees_emails],
        }

        return self.service.events().insert(calendarId="primary", body=event).execute()


    def get_upcoming_events(self, max_results: int = 10) -> UpcomingEventsResponse:
        """
        Fetches upcoming events and returns a structured summary.
        """
        now = datetime.now(datetime.timezone.utc).isoformat()  #  UTC time
        one_week_later = (now + timedelta(days=7)).isoformat()

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=one_week_later,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            )
            .execure()
        )
        events = events_result.get('items', [])
        event_summaries = []

        for event in events:
            event_summaries.append(EventSummary(
                summary=event.get('summary', 'No Title'),
                start_time=event['start'].get('dateTime') or event['start'].get('date'),
                end_time=event['end'].get('dateTime') or event['end'].get('date'),
                organizer_name=event.get('organizer', {}).get('displayName'),
                location=event.get('location'),
                html_link=event.get('htmlLink')
            ))
        
        return UpcomingEventsResponse(events=event_summaries)
        