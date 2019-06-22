from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def main():
    """
    Adapted from Google Sheets quickstart (https://developers.google.com/sheets/api/quickstart/python)
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    print("Attemping to existing credentials from file...")
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired, refreshing...", end=" ")
            creds.refresh(Request())
            print("Done.")
        else:
            print("Authenticating with details from 'credentials.json'...", end=" ")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
            print("Done.")

        # Save the credentials for the next run
        print("Writing updated credentials to 'token.pickle'...", end=" ")
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
            print("Done.")

    else:
        print("Up-to-date credentials loaded from 'token.pickle'.")


if __name__ == "__main__":
    main()
