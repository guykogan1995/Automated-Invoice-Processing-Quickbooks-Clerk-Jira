from intuitlib.client import AuthClient
import requests
import base64

TOKEN_URL = 'type in'
CLIENT_ID = 'type in'
CLIENT_SECRET = 'type in'
AUTHORIZATION_CODE = 'type in'
REDIRECT_URI = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
SANDBOX_ENVIRONMENT = 'sandbox'
REALM_ID = '4620816365380591410'

# Set up AuthClient for the authorization URL
auth_client = AuthClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    environment=SANDBOX_ENVIRONMENT,
)

auth_header = f"{CLIENT_ID}:{CLIENT_SECRET}"
encoded_auth_header = base64.b64encode(auth_header.encode('utf-8')).decode('utf-8')
auth_value = f'Basic {encoded_auth_header}'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'Authorization': auth_value
}

data = {
    'grant_type': 'authorization_code',
    'code': AUTHORIZATION_CODE,
    'redirect_uri': REDIRECT_URI,
    'environment': SANDBOX_ENVIRONMENT,
    'realmId': REALM_ID  # Include the realm ID in the request
}

response = requests.post(TOKEN_URL, headers=headers, data=data)

if response.status_code == 200:
    access_token = response.json().get('access_token')
    print(f"Access Token: {access_token}")
else:
    print(f"Failed to retrieve access token. Status code: {response.status_code}")
    print(response.text)
