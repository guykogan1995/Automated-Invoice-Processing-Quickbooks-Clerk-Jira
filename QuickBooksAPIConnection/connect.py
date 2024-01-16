"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to the QuickBooks API and pulls
    in orders that have been paid to be processed into Jira and Clerk.
"""
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import base64
import requests

# Constants which will be used to authenticate within Quickbooks
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
SANDBOX_ENVIRONMENT = 'sandbox'


class Connection:
    """
    This is the Connection class of QuickBooks
    """

    def __init__(self, auth=""):
        """
        This is the constructor for the Connection class and runs the connection as well
        as initializes the dictionary payed_transactions

        param auth: an optional authentication code argument not required for first run,
            after user has authenticated via URL, the user will need to put into the constructor.
        """
        self.payed_transactions = {}
        self.run_connection(auth)

    def refresh_access_token(self, refresh_token, client_id, client_secret):
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
        auth_header2 = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        headers2 = {
            'Authorization': f'Basic {auth_header2}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        response2 = requests.post(token_endpoint, headers=headers2, data=data)
        if response2.status_code == 200:
            new_tokens = response2.json()
            return new_tokens['access_token'], new_tokens['refresh_token']
        else:
            raise Exception(f"Failed to refresh token: {response2.text}")

    def get_transactions(self, url, headers):
        """This function takes 2 strings: url, and headers
        It will then create a dictionary with all the transactions that have been payed

        param url: String, This is the url access point to the quickbooks company\n
        param headers: Dictionary, the header in order to access quickbooks\n


        updates: payed_transactions, A dictionary that stores ID(will have RFR-<ID> when accessed into Jira),
        Total Amount, Customer Name, and Clerk Reference.
        """
        response2 = requests.get(url, headers=headers)
        invoices2 = response2.json()

        transactions = invoices2['QueryResponse']['Invoice']
        for transaction in transactions:
            if transaction['Balance'] == 0.0:
                private_note = str(transaction.get("PrivateNote"))
                start = private_note.rfind("Clerk Invoice Number: ")
                end = private_note.find(" Clerk Invoice Link:")
                unique_id = private_note[start + len("Clerk Invoice Number: "): end]
                start = private_note.rfind("/")
                clark_id = private_note[start + 1:]
                amount = transaction.get("TotalAmt")
                name = transaction["CustomerRef"].get("name")
                # email = transaction.get("BillEmail")
                invoice_dictionary = {"ID": unique_id, "Total Amount": amount,
                                      "Customer Name": name, "Clerk Reference": clark_id}
                self.payed_transactions[unique_id] = invoice_dictionary

    def run_connection(self, auth_code=""):
        """This function takes 1 optional strings: auth_code
        It will create the connection to quickbooks by first making the user sign in,
        and then supplying an authorization code

        param auth_code: String, This is an optional string which is not needed the first time
        you run, once sign in is prompted an authorization code will be given to be input into
        this function and allow connection\n


        prints: status code and if connection was successful
        """
        auth_client = AuthClient(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            environment=SANDBOX_ENVIRONMENT,
        )
        url = auth_client.get_authorization_url([Scopes['ACCOUNTING']])
        print(url)
        realm_id = '4620816365380591410'
        auth_client.get_bearer_token(auth_code, realm_id=realm_id)
        base_url = 'https://sandbox-quickbooks.api.intuit.com'
        url = '{0}/v3/company/{1}/query?query=select * from Invoice'.format(base_url, auth_client.realm_id)
        auth_header = 'Bearer {0}'.format(auth_client.access_token)
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.get_transactions(url, headers)
            print(f"successfully fetched invoices from QuickBooks: response 200")
        else:
            print(f"Failed to fetch invoices: {response.text}")
