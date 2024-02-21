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
SANDBOX_ENVIRONMENT = 'sandbox'
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
        with open("Credentials.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            if "QuickBooks:" in line:
                continue
            else:
                key, value = line.split()
                creds[key] = value
        con = sqlite3.connect("Jira-Quickbooks-sql.db")
        cur = con.cursor()
        res = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_id';")
        self.CLIENT_ID = res.fetchone()[1]
        res = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_secret';")
        self.CLIENT_SECRET = res.fetchone()[1]
        res = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'realm_id';")
        self.REALM_ID = res.fetchone()[1]
        res = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'realm_id';")
        self.AUTHORIZATION = res.fetchone()[1]
        con.close()
        self.auth_client = AuthClient(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            environment=SANDBOX_ENVIRONMENT,
        )
        self.REFRESH_TOKEN = ''
        self.status = self.run_connection(auth, refresh)

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
        con = sqlite3.connect("Jira-Quickbooks-sql.db")
        cur = con.cursor()
        try:
            if len(invoices2['QueryResponse']) == 0:
                transactions = []
            else:
                transactions = invoices2['QueryResponse']['Invoice']
            for transaction in transactions:
                quickbooks_num = transaction.get("Id")
                res = cur.execute(f"SELECT jira_id FROM Invoices WHERE quickbooks_id = '{quickbooks_num}'")
                unique_id = res.fetchone()[0]
                res = cur.execute(f"SELECT is_invoiced  FROM Invoices WHERE jira_id = '{unique_id}';")
                try:
                    is_done = res.fetchone()[0]
                except TypeError:
                    continue
                if is_done == '1':
                    continue
                amount = transaction.get("TotalAmt")
                name = transaction["CustomerRef"].get("name")
                invoice_dictionary = {"ID": unique_id, "Total Amount": amount,
                                      "Customer Name": name,
                                      "QuickBooks Ref": quickbooks_num}
                self.payed_transactions[unique_id] = invoice_dictionary
            con.close()
        except KeyError:
            self.payed_transactions = []

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

        if creds["AUTHORIZATION"] == "<Fill-this-out-after-first-run>":
            print("Need to click on link")
            exit(1)
        else:
            auth_code = creds["AUTHORIZATION"]
            if auth_2 == "":
                self.auth_client.get_bearer_token(auth_code, realm_id=self.REALM_ID)
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
            #  move the main into server / test on aws
            con = sqlite3.connect("Jira-Quickbooks-sql.db")
            cur = con.cursor()
            res = cur.execute("SELECT quickbooks_id FROM Invoices WHERE is_invoiced = '0'")
            qb_ids = res.fetchall()
            qb_ids = str([i[0] for i in qb_ids])
            qb_ids = qb_ids[1:-1]
            query = f"SELECT * FROM Invoice WHERE Balance = '0' AND Id IN ({qb_ids})"
            url2 = "{0}/v3/company/{1}/query?query={2}".format(base_url, self.auth_client.realm_id, query)
            self.get_transactions(url2, headers)
            if len(self.payed_transactions) == 0:
                print("No completed transactions")
            else:
                print(f"successfully fetched invoices from QuickBooks: response 200")
        else:
            print(f"Failed to fetch invoices: {response.text}")
        return response.status_code
