"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to the QuickBooks and checks if orders have been paid
    in Sqllite if the order has been paid then Jira is updated
"""
import sqlite3
import json
import SqllitePushingToQuickbooks.connect
import QuickBooksAPIConnection.connect
import JiraAPIConnection.connect
import logging
import Test.test
from logging.handlers import TimedRotatingFileHandler
from http.server import BaseHTTPRequestHandler, HTTPServer


class RequestHandler(BaseHTTPRequestHandler):
    #qb_connect = None
    def do_POST(self):
        print("Received POST request")
        if self.path == '/api/test':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = post_data.decode('utf-8')
            #print(type(post_data))
            try:
                print("Sending request to parse")
                print("post_data")
                # Returns the quickbook payment link if successful
                link = SqllitePushingToQuickbooks.connect.parse_post_request(post_data)
                
                if link is None:
                    response = {"message": "Online payment is not enabled for this client."}
                else:
                    response = {"link": link}

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Sending the JSON response
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
                JiraAPIConnection.connect.move_jira_tickets()

            except Exception as e:
                self.send_error(500, str(e))


def run_server(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Server running on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    str_reports_arr = []
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

    run_server()
    #JiraAPIConnection.connect.move_jira_tickets()
