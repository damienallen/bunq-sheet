from __future__ import print_function
from datetime import datetime
import logging
import logging.config
import pickle
import os
import json

from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from secret import SPREADSHEET_ID


# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

COLS = {
    "year": 0,
    "year_subtotal": 1,
    "jan": 2,
    "feb": 3,
    "mar": 4,
    "apr": 5,
    "may": 6,
    "jun": 7,
    "jul": 8,
    "aug": 9,
    "sep": 10,
    "oct": 11,
    "nov": 12,
    "dec": 13,
}


def main(sheet):
    """
    Process bunq data and inject into Sheet
    """

    # Fetch sheet values for current year
    sheet_name = f"{datetime.now().year}"
    result = (
        sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=sheet_name).execute()
    )
    current_values = result.get("values", [])

    # Process rows

    if not current_values:
        print("No data found.")
    else:
        account_data = process_rows(current_values)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "dumps",
            f"account_{timestamp}.json",
        )

        with open(file_path, "w") as json_file:
            json.dump(account_data, json_file, indent=4, sort_keys=True)

        print(account_data)


def process_rows(values):
    """
    Process spreadsheet into referenced dictionary
    """

    data_dict = {"headers": 0, "people": []}

    for row_ind, row in enumerate(values):

        if row_ind == 0:
            data_dict["headers"] = row[1:14]
            data_dict.get("headers")[0] = "ytd_subtotal"

        elif "Base rent" in row:
            data_dict = extract_deposits(data_dict, values, row_ind, "base_rent")

        elif "Bills" in row:
            data_dict = extract_deposits(data_dict, values, row_ind, "bills")

        elif "Transfers" in row:
            data_dict = extract_deposits(data_dict, values, row_ind, "transfers")

        elif "House" in row:
            sub_cats = ["rent", "tax", "misc"]
            data_dict = extract_withdrawls(
                data_dict, values, row_ind, "house", sub_cats
            )

        elif "Utilities" in row:
            sub_cats = ["electric_gas", "water"]
            data_dict = extract_withdrawls(
                data_dict, values, row_ind, "utils", sub_cats
            )

        elif "Subscriptions" in row:
            sub_cats = ["internet", "netflix", "misc"]
            data_dict = extract_withdrawls(data_dict, values, row_ind, "subs", sub_cats)

        else:
            continue

    return data_dict


def extract_deposits(data_dict, values, row_ind, category):
    data_dict[category] = {}
    cursor = row_ind + 1

    while True:

        if not values[cursor]:
            break
        elif "Subtotal" in values[cursor]:
            break

        person = values[cursor][0]
        data_dict[category][person] = []

        for n in range(1, 14):
            try:
                cursor_value = (
                    eur_to_value(values[cursor][n]) if values[cursor][n] else None
                )
                data_dict[category][person].append(cursor_value)
            except IndexError:
                data_dict[category][person].append(None)

        if not person in data_dict["people"]:
            data_dict["people"].append(person)

        cursor += 1

    return data_dict


def extract_withdrawls(data_dict, values, row_ind, category, sub_cats):

    data_dict[category] = {}
    cursor = row_ind + 1

    for sub_cat in sub_cats:
        data_dict[category][sub_cat] = []

        for n in range(1, 14):
            try:
                cursor_value = (
                    eur_to_value(values[cursor][n]) if values[cursor][n] else None
                )
                print(value_to_eur(cursor_value))
                data_dict[category][sub_cat].append(cursor_value)
            except IndexError:
                data_dict[category][sub_cat].append(None)

        cursor += 1

    return data_dict


def eur_to_value(eur_string):
    return float(
        eur_string.replace("\u20ac", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )


def value_to_eur(value):
    return f"\u20ac{value:.2f}".replace(".", ",") if value else None


def fetch_credentials():
    """
    Attempt to fetch credentials from file, refresh if necessary
    """

    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds


if __name__ == "__main__":

    # Initialize loggers
    logging.getLogger("googleapicliet.discovery_cache").setLevel(logging.ERROR)
    logging.config.fileConfig(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "logging.conf")
    )
    logger = logging.getLogger("root")

    # Fetch Sheets credentials and load sheet
    creds = fetch_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    main(sheet)
