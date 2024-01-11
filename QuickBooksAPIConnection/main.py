import time
import schedule
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import base64
import requests

global transactions
payed_transactions = {}


def refresh_access_token(refresh_token, client_id, client_secret):
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
        raise Exception(f"Failed to refresh token: {response.text}")


def get_transactions():
    global transactions
    response2 = requests.get(url, headers=headers)
    invoices2 = response2.json()
    transactions = invoices2['QueryResponse']['Invoice']
    for transaction in transactions:
        if transaction['Balance'] == 0.0:
            invoice_dictionary = {"ID": transaction["Id"], "Total Amount": transaction["TotalAmt"],
                                  "Customer Name": transaction["CustomerRef"]["name"],
                                  "Bill Email": transaction["BillEmail"]["Address"]}
            payed_transactions[transaction["Id"]] = invoice_dictionary


CLIENT_ID = 'ABRfb8HlI2YzXziLnnXqooLXiqI24kKyGPZIgy3X9kkeZ289Tq'
CLIENT_SECRET = 'pQAibk5sRKSbu6Fkk0ujs7vzrqsE0JvbKV2KTcsu'
REDIRECT_URI = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
SANDBOX_ENVIRONMENT = 'sandbox'

auth_client = AuthClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    environment=SANDBOX_ENVIRONMENT,
)
url = auth_client.get_authorization_url([Scopes['ACCOUNTING']])
print(url)

auth_code = 'AB11704932370nmdEo9bhvAeYspKyppvJSZe70CZigamO0BObq'
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
    schedule.every(30).minutes.do(refresh_access_token, auth_client.refresh_token, CLIENT_ID, CLIENT_SECRET)
    schedule.every(30).minutes.do(get_transactions)
    get_transactions()
    while True:
        schedule.run_pending()
        print(payed_transactions)
        print(len(payed_transactions))
        time.sleep(60 * 10)

else:
    print(f"Failed to fetch invoices: {response.text}")
