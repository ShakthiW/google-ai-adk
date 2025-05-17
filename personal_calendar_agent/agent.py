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
from typing import List, Dict, Optional

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
    """
    Retrieves the next num_events events from the user's calendar.
    
    Args:
        num_events (int): The number of events to retrieve. Defaults to 10.

    Returns:
        list: A list of the next num_events events.
    """
    response = ""
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=num_events,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            response = "No upcoming events found."

        # Prints the start and name of the next events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            start_date = dt.datetime.fromisoformat(start)
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            response += f"{start_date_str}, {event['summary']}\n"
            print(f"--- Tool: Get the next {num_events} events. Result: {response} ---")

        return response

    except HttpError as error:
        return f"An error occurred: {error}"


def get_current_timezone():
    """
    Gets the current timezone.
    
    Returns:
        str: The current timezone.
    """
    response = ""
    try:
        response = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        print(f"--- Tool: Get the current timezone. Result: {response} ---")
    except Exception as e:
        response = f"An error occurred: {e}. You can only get the current timezone with this method."
    return response

def add_event_to_calendar(
    summary: str = "No summary",
    start: str = "No start",
    end: str = "No end",
    location: str = "Online",
    description: str = "No description",
    date: str = "No date"
):
    """
    Adds an event to the user's calendar.
    
    Args:
        summary (str): The summary of the event.
        start (str): The start time of the event in the format HH:MM:SS.
        end (str): The end time of the event in the format HH:MM:SS.
        location (str): The location of the event.
        description (str): The description of the event.
        date (str): The date of the event in the format YYYY-MM-DD.

    Returns:
        str: A message indicating that the event has been added.
    """
    print(f"--- Tool: Add an event to the calendar. Args: summary={summary}, start={start}, end={end}, location={location}, description={description}, date={date} ---")
    if date == "No date":
        return "Error: Date must be provided in YYYY-MM-DD format."
    try:
        date_only = dt.datetime.strptime(date, "%Y-%m-%d").date().isoformat()
        start = f"{date_only}T{start}"
        end = f"{date_only}T{end}"
    except Exception as e:
        return f"Error: Invalid date format. {e}"
    
    timezone = get_current_timezone()
    response = ""
    try:
        service = build("calendar", "v3", credentials=creds)
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start,
                "timeZone": timezone
            },
            "end": {
                "dateTime": end,
                "timeZone": timezone
            },
        }
        
        service.events().insert(calendarId="primary", body=event).execute()
        response = "Event added to calendar."
    except HttpError as error:
        response = f"An error occurred: {error}"
    except Exception as e:
        response = f"An error occurred: {e}. You can only add events to your calendar with this method."
    return response

def get_the_date_today():
    """
    Gets the date today.
    
    Returns:
        str: The date today.
    """
    response = ""
    try:
        response = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        print(f"--- Tool: Get the date today. Result: {response} ---")
    except Exception as e:
        response = f"An error occurred: {e}. You can only get the date today with this method."
    return response

root_agent = Agent(
    name="calendar_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the user's calendar and schedule and add events to the calendar"
    ),
    instruction=(
        "You are a helpful assistant that can answer questions about the user's calendar and schedule and add events to the calendar. Ask questions about the missing fields if they are not provided."
        "to add an event to the calendar use the add_event_to_calendar tool."
        "If the user specify a relative date use the get_the_date_today tool to get the date today."
    ),
    tools=[get_next_events, add_event_to_calendar, get_the_date_today],
)

session_service = InMemorySessionService()

APP_NAME = "personal_calendar_agent"
USER_ID = "user_1"
SESSION_ID = "session_001"

session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)
print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name=APP_NAME
)
print(f"Runner created for agent '{runner.agent.name}'.")

if __name__ == "__main__":
    try:
        asyncio.run(runner.run())
    except Exception as e:
        print(f"An error occurred: {e}")
