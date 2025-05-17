import os
import asyncio
import datetime as dt
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

def get_next_events(num_events: int = 10):
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return "No upcoming events found."

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print(f"An error occurred: {error}")

def add_event():
    try:
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": "My Test Event from API",
            "location": "Online",
            "description": "This is a test event from the API",
            "start": {
                "dateTime": "2025-05-17T10:00:00",
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": "2025-05-17T11:00:00",
                "timeZone": "America/New_York"
            },
            "recurrence": [
                "RRULE:FREQ=DAILY;COUNT=5"
            ],
            "attendees": [
                {"email": "test@example.com"},
                {"email": "test2@example.com"},
                {"email": "test3@example.com"}
            ],
            "reminders": {
                "useDefault": False,
                
            }
        }
        
        service.events().insert(calendarId="primary", body=event).execute()
        print("Event added to calendar.")
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    add_event()
