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
from logging.handlers import TimedRotatingFileHandler
from http.server import BaseHTTPRequestHandler, HTTPServer


class RequestHandler(BaseHTTPRequestHandler):
    qb_connect = None
    def do_post(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            response = SqllitePushingToQuickbooks.connect.parse_post_request(post_data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            logic(qb_connect)
        except Exception as e:
            self.send_error(500, str(e))


def run_server(qb_con, server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    RequestHandler.qb_connect = qb_con
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Server running on port {port}...')
    httpd.serve_forever()


def logic(qb_con):
    qb_connect = qb_con
    if qb_connect.status != 200:
        logger.error('Unable to connect to quickbooks, status: ' + str(qb_connect.status))
        exit(1)
    logger.info("Successfully connected to QuickBooks")
    con = sqlite3.connect("Jira-Quickbooks-sql.db")
    cur = con.cursor()
    for transaction in qb_connect.payed_transactions:
        print("-------------------------------------------------")
        jira_success = JiraAPIConnection.connect.update_jira(transaction)
        if jira_success == 204:
            res = cur.execute(f"UPDATE Invoices SET is_invoiced = '1' WHERE jira_id = '{transaction}';")
            logger.info('Successfully changed Jira ticket: ' + transaction + " -> to done")
            qb_ref = qb_connect.payed_transactions[transaction]["QuickBooks Ref"]
            # remove sqllite code push does this
            cur.execute(f"UPDATE Invoices SET quickbooks_id = '{qb_ref}' WHERE jira_id = '{transaction}';")
            logger.info("-------------------------------------------------\n"
                                   "Successfully moved tickets ------>\n"
                                   f"Jira Reference: {transaction}\n"
                                   f"QuickBooks ID: {qb_ref}\n"
                                   f"-------------------------------------------------")
            str_reports_arr.append("-------------------------------------------------\n"
                                   "Successfully moved tickets ------>\n"
                                   f"Jira Reference: {transaction}\n"
                                   f"QuickBooks ID: {qb_ref}\n"
                                   f"-------------------------------------------------")
            print("Successfully moved tickets ------>")
            print(f"""Jira Reference: {transaction}
                        QuickBooks ID: {qb_ref}""")
            print("------> To Completed")
            con.commit()
        else:
            logger.warning('Jira ticket was not able to be changed to done: ' + transaction)
        print("-------------------------------------------------")
    if len(str_reports_arr) != 0:
        logger.info("Changed " + str(len(str_reports_arr)) + " tickets to invoiced.")
        logger.info(str_reports_arr)
    else:
        logger.info("No tickets were changed")
        # qb_connect.run_connection(new_access_token, new_refresh_token)
    con.close()


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
    qb_connect = QuickBooksAPIConnection.connect.Connection()
    new_access_token, new_refresh_token = QuickBooksAPIConnection.connect.refresh_access_token(qb_connect.REFRESH_TOKEN,
                                                                                       qb_connect.CLIENT_ID,
                                                                                       qb_connect.CLIENT_SECRET)
    con = sqlite3.connect("Jira-Quickbooks-sql.db")
    cur = con.cursor()
    cur.execute(f"UPDATE Credentials SET value = '{new_refresh_token}' WHERE identifier = 'refresh_token';")
    con.commit()
    con.close()
    run_server(qb_connect)
