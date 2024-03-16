"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to the QuickBooks API and pulls
    in orders that have been paid to be processed into Jira and the DB.
"""

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import base64
import requests
import sqlite3


# Constants which will be used to authenticate within Quickbooks
REDIRECT_URI = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
SANDBOX_ENVIRONMENT = 'production'
creds = {}


def refresh_access_token(refresh_token, client_id, client_secret):
    """This function takes 3 strings: refresh token, client id, and client secret
    and returns the refresh token, and access token enabling the connection to be allowed
    to be connected for another hour

    param refresh_token: String, this token allows the connection to be open for 1 hour\n
    param client_id: String, this is the client id of the quickbooks company\n
    param client_secret: String, this is the secret client id of the quickbooks company\n

    returns: String, new access token and refresh token allowing the connection to be active
    for another hour
    """

    token_endpoint = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    auth_header = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(token_endpoint, headers=headers, data=data)

    if response.status_code == 200:
        new_tokens = response.json()
        return new_tokens['access_token'], new_tokens['refresh_token']
    else:
        raise Exception(f"Failed to refresh token: {response.text}")


def manual_oauth_flow():

    conn = sqlite3.connect('Jira-Quickbooks-sql.db')
    cur = conn.cursor()
    CLIENT_ID = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_id';").fetchone()[1]
    CLIENT_SECRET = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_secret';").fetchone()[1]
    realm_id = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'realm_id';").fetchone()[1]
    conn.close()

    # Set up AuthClient for the authorization URL
    auth_client = AuthClient(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            environment=SANDBOX_ENVIRONMENT,
            )
    auth_url = auth_client.get_authorization_url([Scopes['ACCOUNTING']])
    print("Please go to the following URL and authorize the application:", auth_url)

    # Prompt the user to enter the authorization code
    auth_code = input("Enter the authorization code: ")

    # Exchange the authorization code for tokens
    auth_client.get_bearer_token(auth_code, realm_id=realm_id)
    access_token = auth_client.access_token
    refresh_token = auth_client.refresh_token

    if access_token and refresh_token:
        return {"access_token":access_token, 
                    "refresh_token": refresh_token}
    else:
        print("Failed to obtain tokens")
        return None
