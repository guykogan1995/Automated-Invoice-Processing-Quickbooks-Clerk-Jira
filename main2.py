from flask import Flask, request, jsonify, abort
import sqlite3
import logging
from logging.handlers import TimedRotatingFileHandler
import json
# Assuming these are your custom modules
import SqllitePushingToQuickbooks.connect
import QuickBooksAPIConnection.connect
import JiraAPIConnection.connect
import JiraAPIConnection.openforms
from requests.auth import HTTPBasicAuth
from JiraAPIConnection.openforms import CONFIG_BC, CONFIG_BASIC

app = Flask(__name__)


@app.route('/api/test', methods=['POST'])
def handle_test():
    # Reading raw data as string
    post_data = request.data.decode('utf-8')  # Decodes data to string using UTF-8
    print("Received POST request")
    print("Post Data:", post_data)  # Debugging print to show raw post data

    try:
        print("Sending request to parse")
        # Assuming parse_post_request function expects a string and processes it
        link = SqllitePushingToQuickbooks.connect.parse_post_request(post_data)

        if link is None:
            response = {"message": "Online payment is not enabled for this client."}
        else:
            response = {"link": link}

        return jsonify(response)

    except Exception as e:
        # If there's an error, return a 500 Internal Server Error with the exception message
        abort(500, description=str(e))

@app.route('/api/route2', methods=['POST'])
def handle_route2():
    data = request.get_json()  # Parses the JSON payload directly into a dictionary
    if not data or 'key' not in data:
        return jsonify({'error': 'Invalid or missing data'}), 400
    
    jira_key = data['key']

    print("Received data on /api/route2:", data)
    print("Jira key:", jira_key)
    
    with sqlite3.connect('Jira-Quickbooks-sql.db') as conn:
        cur = conn.cursor()
        identifiers = ('jira_id', 'cloud_id')
        placeholders = ', '.join(['?'] * len(identifiers))
        cur.execute(f"SELECT identifier, value FROM Credentials WHERE identifier IN ({placeholders})", identifiers)
        credentials = {row[0]: row[1] for row in cur.fetchall()}

    # Make the API call using the JiraAPIConnection
    email = 'tech@redfolderresearch.com'
    forms_response = JiraAPIConnection.connect.manage_jira_forms(jira_key, credentials['cloud_id'], email, credentials['jira_id'])
    JiraAPIConnection.connect.move_jira_tickets()
    # Process the API response
    return jsonify(forms_response)


@app.route('/api/openforms', methods=['POST'])
def handle_openforms():
    data = request.get_json()  # Parses the JSON payload directly into a dictionary
    if not data or 'key' not in data:
        return jsonify({'error': 'Invalid or missing data key'}), 400

    jira_key = data['key']

    print("Received data on /api/openforms:", data)
    print("Jira key:", jira_key)

    with sqlite3.connect('Jira-Quickbooks-sql.db') as conn:
        cur = conn.cursor()
        identifiers = ('jira_id', 'cloud_id')
        placeholders = ', '.join(['?'] * len(identifiers))
        cur.execute(f"SELECT identifier, value FROM Credentials WHERE identifier IN ({placeholders})", identifiers)
        credentials = {row[0]: row[1] for row in cur.fetchall()}

    # Make the API call using the JiraAPIConnection
    email = 'tech@redfolderresearch.com'
    auth = HTTPBasicAuth(email, credentials['jira_id'])

    if jira_key.startswith("BC"):
        response = JiraAPIConnection.openforms.process_forms(jira_key, credentials['cloud_id'], CONFIG_BC, auth)
    else:
        response = JiraAPIConnection.openforms.process_forms(jira_key, credentials['cloud_id'], CONFIG_BASIC, auth)
        
    # Process the API response
    return jsonify(response)



if __name__ == '__main__':
    # Configure logging
    logger = logging.getLogger('my_logger')
    handler = TimedRotatingFileHandler(
        "Jira-Quickbooks-Sync.log",
        when="D",
        interval=7,
        backupCount=1)
    log_format = '%(asctime)s [%(process)d]: %(message)s'
    handler.setFormatter(logging.Formatter(log_format, datefmt="%d-%m-%Y %H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info('Connecting to QuickBooks...')
    
    # Connect to QuickBooks and Jira, initialize tokens and such
    try:
        with sqlite3.connect('Jira-Quickbooks-sql.db') as conn:
            cur = conn.cursor()
            # Fetching credentials in a more secure way
            identifiers = ('client_id', 'client_secret', 'refresh_token', 'realm_id', 'jira_cred')
            placeholders = ', '.join(['?'] * len(identifiers))
            cur.execute(f"SELECT identifier, value FROM Credentials WHERE identifier IN ({placeholders})", identifiers)
            credentials = {row[0]: row[1] for row in cur.fetchall()}

            # Assuming QuickBooksAPIConnection methods handle exceptions internally and log appropriately
            accessToken, new_refresh_token = QuickBooksAPIConnection.connect.refresh_access_token(
                credentials['refresh_token'], credentials['client_id'], credentials['client_secret'])

            # Test the new access token with a generic GET request to QuickBooks
            is_valid, data_or_error = QuickBooksAPIConnection.connect.test_access_token(accessToken, credentials['realm_id'])
            if is_valid:
                # If successful, update the refresh token in the database
                cur.execute("UPDATE Credentials SET value = ? WHERE identifier = 'refresh_token';", (new_refresh_token,))
                conn.commit()
                print("Access token is valid. Data:", data_or_error)
            else:
                print("Access token might be invalid or an error occurred:", data_or_error)
                logger.info('Refreshing token failed, performing manual OAuth flow...')
                print('Refreshing token failed, performing manual OAuth flow...')
                tokens = QuickBooksAPIConnection.connect.manual_oauth_flow()
                cur.execute("UPDATE Credentials SET value = ? WHERE identifier = 'refresh_token';", (tokens['refresh_token'],))

                conn.commit()
    except Exception as e:
        logger.error('An error occurred during token refresh: ' + str(e))
    finally:
        conn.close()
    # Start Flask application
    app.run(host='0.0.0.0', port=8080)

