"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to Jira and changes the tickets
    to Invoice complete after Clerk has been processed.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import sqlite3
import QuickBooksAPIConnection.connect
import JiraAPIConnection.connect
import logging

logger = logging.getLogger(__name__)

def move_jira_tickets():
    try:
        with sqlite3.connect('Jira-Quickbooks-sql.db') as conn:
            cur = conn.cursor()
            # Fetching credentials in a more secure way
            identifiers = ('client_id', 'client_secret', 'refresh_token', 'realm_id', 'jira_id')
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
    

    paid_transactions = QuickBooksAPIConnection.connect.get_paid_transactions(accessToken, credentials['realm_id'])
    logger.info(f'Paid transactions: {paid_transactions}')    
    if paid_transactions is not None:
        try:
            for jira_id, quickbooks_id in paid_transactions.items():
                print("-------------------------------------------------")
                try:
                    jira_success = update_jira(jira_id, credentials['jira_id'])
                    if jira_success == 204:
                        # Using parameterized queries to prevent SQL injection
                        res = cur.execute("UPDATE Invoices SET is_invoiced = 1 WHERE jira_id = ?;", (jira_id,))
                        logger.info(f'Successfully changed Jira ticket: {jira_id} -> to done')
                        logger.info(f"Successfully moved tickets ------>\nJira Reference: {jira_id}\nQuickBooks ID: {quickbooks_id}\n-------------------------------------------------")
                        print(f"Successfully moved tickets ------> Jira Reference: {jira_id}, QuickBooks ID: {quickbooks_id} -> To Completed")
                        conn.commit()  # Consider if it's more efficient for your use case to commit outside the loop
                    else:
                        logger.warning(f'Jira ticket was not able to be changed to done: {jira_id}')
                except Exception as e:
                    logger.error(f"Error updating ticket {jira_id} or committing to database: {e}")
                print("-------------------------------------------------")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            conn.close()
    else:
        logger.info("No paid transactions found")


def update_jira(id_to_update, auth_id):
    """
    This function updates Jira tickets to Invoice complete

    :param id_to_update: The Jira ID to update
    :return: the response status code 204 is ticket was successfully updated
    """

    url = f"https://redfolderresearch.atlassian.net/rest/api/3/issue/{id_to_update}/transitions"
    auth = HTTPBasicAuth("tech@redfolderresearch.com", auth_id)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    invoiced_status_check = requests.request(
    "GET",
    f"https://redfolderresearch.atlassian.net/rest/api/2/issue/{id_to_update}",
    headers=headers,
    auth=auth
    )
    if invoiced_status_check.status_code == 200:
        try:
            issue_status = json.loads(invoiced_status_check.text)['fields']['status']['id']
            status_text = json.loads(invoiced_status_check.text)['fields']['status']['name']
            if issue_status == '6': #paid
                return 204
            if issue_status == '10101': #Finance
                payload = json.dumps({"transition": {"id": "451"}})
                requests.request(
                        "POST",
                        url,
                        data=payload,
                        headers=headers,
                        auth=auth
                        )
            if (issue_status == "10102") or (issue_status == "10101"): #finance status
                payload = json.dumps({"transition": {"id": "431" }})
                paid_status = requests.request(
                    "POST",
                    url,
                    data=payload,
                    headers=headers,
                    auth=auth
                )
                if (paid_status.status_code == 204) or (paid_status.status_code == 200):
                    return 204
                else:
                    logger.warning(f"Failed to update Jira ticket {id_to_update}, Ticket not in correct status, current status: {status_text} and {issue_status}")
            elif (issue_status != "10102") and (issue_status != "10101") and (issue_status != "6"):
                logger.warning(f"Failed to update Jira ticket {id_to_update}, Ticket not in correct status, current status: {status_text}")
                return invoiced_status_check.status_code
        except KeyError:
            logger.warning(f"Failed to update Jira ticket {id_to_update}, Ticket does not exist")
            return invoiced_status_check.status_code

    return invoiced_status_check.status_code

