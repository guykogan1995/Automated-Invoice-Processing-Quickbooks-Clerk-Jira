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
REDIRECT_URI = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
SANDBOX_ENVIRONMENT = 'sandbox'
creds = {}


class Connection:
    """
    This is the Connection class of QuickBooks
    """

    def __init__(self, auth="", refresh=""):
        """
        This is the constructor for the Connection class and runs the connection as well
        as initializes the dictionary payed_transactions

        param auth: an optional authentication code argument not required for first run,
            after user has authenticated via URL, the user will need to put into the constructor.
        """
        self.payed_transactions = {}
        self.memo = {}

        with open("Credentials.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            if "Clerk:" in line:
                break
            if "QuickBooks:" in line:
                continue
            else:
                key, value = line.split()
                creds[key] = value
        self.CLIENT_ID = creds['CLIENT_ID']
        self.CLIENT_SECRET = creds["CLIENT_SECRET"]
        self.auth_client = AuthClient(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            environment=SANDBOX_ENVIRONMENT,
        )
        self.REFRESH_TOKEN = ''
        self.run_connection(auth, refresh)

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
                if "\nJira Invoiced Status: True" in private_note:
                    continue
                start = private_note.rfind("Clerk Invoice Number: ")
                end = private_note.find("\n")
                unique_id = private_note[start + len("Clerk Invoice Number: "): end]
                start = private_note.rfind("/")
                clark_id = private_note[start + 1:]
                quickbooks_id = transaction.get("Id")
                self.memo[quickbooks_id] = {"note": private_note,
                                            "sync": transaction["SyncToken"]
                                            }
                amount = transaction.get("TotalAmt")
                name = transaction["CustomerRef"].get("name")
                invoice_dictionary = {"ID": unique_id, "Total Amount": amount,
                                      "Customer Name": name, "Clerk Reference": clark_id,
                                      "QuickBooks Ref": quickbooks_id}
                self.payed_transactions[unique_id] = invoice_dictionary

    def run_connection(self, auth_2="", refresh=""):
        """This function takes 1 optional strings: auth_code
        It will create the connection to quickbooks by first making the user sign in,
        and then supplying an authorization code

        param auth_code: String, This is an optional string which is not needed the first time
        you run, once sign in is prompted an authorization code will be given to be input into
        this function and allow connection\n


        prints: status code and if connection was successful
        """
        url = self.auth_client.get_authorization_url([Scopes['ACCOUNTING']])
        print(url)
        if creds["REALM_ID"] == "<Fill-this-out-after-first-run>":
            realm_id = ""
        else:
            realm_id = creds["REALM_ID"]
        if creds["AUTHORIZATION"] == "<Fill-this-out-after-first-run>":
            print("Need to click on link")
            exit(1)
        else:
            auth_code = creds["AUTHORIZATION"]
            if auth_2 == "":
                self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
        if auth_2 != "":
            auth_code = auth_2
            self.auth_client.access_token = auth_code
            self.auth_client.refresh_token = refresh
        self.REFRESH_TOKEN = self.auth_client.refresh_token
        base_url = 'https://quickbooks.api.intuit.com'
        url = '{0}/v3/company/{1}/query?query=select * from Invoice'.format(base_url, self.auth_client.realm_id)
        auth_header = 'Bearer {0}'.format(self.auth_client.access_token)
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.get_transactions(url, headers)
            print(self.get_transactions)
            if len(self.payed_transactions) == 0:
                print("No completed transactions")
            print(f"successfully fetched invoices from QuickBooks: response 200")
        else:
            print(f"Failed to fetch invoices: {response.text}")

    def update_invoice(self, quick_id):
        base_url = 'https://quickbooks.api.intuit.com'
        url = '{0}/v3/company/{1}/invoice?operation=update'.format(base_url, self.auth_client.realm_id)
        auth_header = 'Bearer {0}'.format(self.auth_client.access_token)
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            "SyncToken": str(int(self.memo[quick_id]["sync"]) + 1),
            "Id": quick_id,
            "sparse": True,
            "PrivateNote": self.memo[quick_id]["note"] + "\nJira Invoiced Status: True"
        }
        response3 = requests.post(url, headers=headers, json=data)
        return response3.status_code
