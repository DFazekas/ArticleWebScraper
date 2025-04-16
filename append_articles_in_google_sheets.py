"""
Module for appending scraped articles to a Google Sheet.
"""

import os
import sys
import requests
from dotenv import load_dotenv


def get_access_token(jwt_filename="jwt.txt"):
    """
    Reads a JWT from file and exchanges it for an access token.

    Returns:
        str: The obtained access token.

    Raises:
        RuntimeError: If the JWT cannot be read or the token exchange fails.
    """
    # Loads environment variables from the .env file into os.environ
    load_dotenv()

    # Read your JWT token from a file called "jwt.txt".
    print("Reading JWT token from file ...")
    try:
        with open(jwt_filename, "r", encoding="utf-8") as jwt_file:
            jwt_token = jwt_file.read().strip()
    except Exception as e:
        raise RuntimeError(f"Error reading JWT token: {e}") from e

    print("Successfully obtained JWT token.")

    token_url = "https://oauth2.googleapis.com/token"

    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token
    }

    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Send the POST request to obtain an access token.
    print("Exchanging JWT for Access Token ...")
    token_response = requests.post(
        token_url,
        data=token_payload,
        headers=token_headers,
        timeout=10)
    if token_response.status_code != 200:
        error_msg = f"Failed to obtain access token: {token_response.text}"
        raise RuntimeError(error_msg)

    # Extract the access token.
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise RuntimeError("Access token not found in the response.")

    print("Successfully obtained Access Token.")
    return access_token


def load_articles(file_path="articles.txt"):
    """
    Reads articles from a file and parses them into a list.

    Returns:
        list: A list of rows where each row is formatted as ["", "", link, title].
              If no articles are found, the list is empty.

    Raises:
        RuntimeError: If there is an error reading the file.
    """
    articles = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise RuntimeError(f"Error reading {file_path}: {e}") from e

    # Split into blocks based on the dashed separator.
    blocks = content.split("----------------------------------------")
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        title = None
        link = None
        # Process each line in the block.
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("Title:"):
                title = line[len("Title:"):].strip()
            elif line.startswith("Link:"):
                link = line[len("Link:"):].strip()
        # If both title and link are found, build a row.
        if title and link:
            # To force insertion into columns C and D,
            # include two empty strings for columns A and B.
            articles.append(["", "", link, title])

    if not articles:
        print("No articles found to append.")
    else:
        print(f"Found {len(articles)} article(s) to append.")

    return articles


def append_articles(articles, access_token):
    """
    Appends the given articles to the Google Sheet.

    Args:
        articles (list): List of articles formatted as rows.
        access_token (str): OAuth 2.0 access token.

    Returns:
        dict: The JSON response from the Sheets API.

    Raises:
        RuntimeError: If appending the data fails.
    """
    sheet_name = os.getenv("SPREADSHEET_SHEET_NAME")
    cell_range = os.getenv("SPREADSHEET_CELL_RANGE")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")

    if not (sheet_name and cell_range and spreadsheet_id):
        raise RuntimeError(
            "Missing one or more required env variables: "
            "SPREADSHEET_SHEET_NAME, SPREADSHEET_CELL_RANGE, SPREADSHEET_ID.")

    # Build the URL.
    range_name = f"{sheet_name}!{cell_range}"
    append_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/{range_name}:append?valueInputOption=USER_ENTERED"
    )

    # Build headers, including the authorization bearer token.
    sheets_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Build the request body.
    body = {"values": articles}

    # Send the append POST request.
    print("Appending data to Google Sheets ...")
    append_response = requests.post(
        append_url, headers=sheets_headers, json=body, timeout=10
    )
    if append_response.status_code != 200:
        error_msg = f"Error appending data to Google Sheets: {append_response.text}"
        raise RuntimeError(error_msg)

    print("Successfully appended data to Google Sheets.")
    return append_response.json()


def run_append_articles():
    """
    Runs the complete process: obtains an access token, loads articles from file,
    and appends them to Google Sheets.
    """
    access_token = get_access_token()
    articles = load_articles()
    if articles:
        return append_articles(articles, access_token)
    return None


def main():
    """
    Command-line entry point for appending articles to Google Sheets.
    """
    try:
        run_append_articles()
    except RuntimeError as e:
        # Catch any unexpected exceptions
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
