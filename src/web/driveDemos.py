from __future__ import print_function

raise NotImplementedError(f"{__file__} is not implemented.")

import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def getFiles(secretFile):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                secretFile, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return

        result = []
        for item in items:
            name = item["name"]
            if "Cinnamon" in name[0:len("Cinnamon")]:
                result.append(name)
            #print(u'{0} ({1})'.format(item['name'], item['id']))
        return result
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def progress(secretFile):
    errors = []
    result = {}

    for fileName in getFiles(secretFile):
        parts = fileName.split("_")
        attempts = int(parts[1].split(".")[0])
        parts = parts[0].split("-")

        if len(parts) != 5:
            errors.append(fileName)
            continue

        result[fileName] = {
            "attempts":     attempts,
            "category":     parts[4],
            "difficulty":   parts[3],
            "player":       parts[0],
            "map":          parts[2],
            "wad":          parts[1]
        }
        print(type(result[fileName]))

    return findNexts(byWad(result, errors))


def byWad(demos, errors):
    result = {}
    for fileName, entry in demos.items():
        wadName = entry["wad"]

        if wadName not in result:
            result[wadName] = []

        result[wadName].append(entry["map"])

    for name, _ in result.items():
        result[name].sort()

    return result, errors

def findNexts(progress, errors):
    types = {}
    for wadName, maps in progress.items():
        types[wadName] = "doom" if maps[0][0] == "e" else "doom2"

def driveDemos():
    raise NotImplementedError(f"{__name__} is not implemented.")
