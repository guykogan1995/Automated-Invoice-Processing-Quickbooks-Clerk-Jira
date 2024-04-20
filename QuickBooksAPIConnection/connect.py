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


def test_access_token(access_token, company_code):
    """
    Tests if the provided access token is valid by attempting to fetch a single invoice.

    :param access_token: The access token to be tested.
    :param company_code: The company code needed for the QuickBooks API request.
    :return: A tuple containing a boolean indicating whether the token is valid, and the data or error message.
    """
    base_url = 'https://quickbooks.api.intuit.com'
    url = f"{base_url}/v3/company/{company_code}/query?query=SELECT * FROM Invoice MAXRESULTS 1"
    auth_header = f'Bearer {access_token}'
    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            # Assuming the token is valid if a 200 status code is received
            return True, response.json()
        else:
            # If the status code is not 200, assume the token is invalid
            print(f"Failed to fetch invoices: {response.text}")
            return False, response.text
    except Exception as e:
        # Handle exceptions for network issues or JSON parsing errors
        print(f"An error occurred: {e}")
        return False, str(e)


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


def get_paid_transactions(accessToken, companyCode):
    """This function takes 2 strings: access token, and company code
    param accessToken: String, This is the access token for qb\n
    param companyCode: int this is the company code\n
    """
    con = sqlite3.connect("Jira-Quickbooks-sql.db")
    cur = con.cursor()
    res = cur.execute("SELECT quickbooks_id FROM Invoices WHERE is_invoiced = '0'")
    qb_ids = res.fetchall()

    base_url = 'https://quickbooks.api.intuit.com'
    formatted_ids = ', '.join([f"'{id[0]}'" for id in qb_ids])  # Format invoice IDs for the query
    query = f"SELECT Id, TotalAmt FROM Invoice WHERE Balance = '0' AND Id IN ({formatted_ids})"
    url = f"{base_url}/v3/company/{companyCode}/query?query={query}"
    headers = {
        'Authorization': f'Bearer {accessToken}',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response was an error
        invoices_data = response.json()
        print(invoices_data['QueryResponse'])
        if len(invoices_data['QueryResponse']) == 0:
            print("No invoices found")
            return None
        invoices_dict = {}

        for invoice in invoices_data['QueryResponse']['Invoice']:
            quickbooks_id = invoice['Id']
            jira_id_query = cur.execute("SELECT jira_id FROM Invoices WHERE quickbooks_id = ?", (quickbooks_id,))
            jira_id = jira_id_query.fetchone()

            if jira_id:
                invoices_dict[jira_id[0]] = quickbooks_id

        con.close()
        return invoices_dict if invoices_dict else None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except KeyError:
        print("Unexpected response format")
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        con.close()
