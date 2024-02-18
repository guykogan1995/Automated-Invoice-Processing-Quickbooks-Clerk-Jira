"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to the QuickBooks and checks if orders have been paid
    if they are paid the reference to clerk and Jira is grabbed, In both cases, the script
    will change in both of those the tickets to complete.
"""
import time

import ClerkAPIConnection.connect
import QuickBooksAPIConnection.connect
import JiraAPIConnection.connect
import logging
from logging.handlers import TimedRotatingFileHandler
import time


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
    logger.setLevel(1)
    logger.info('Connecting to QuickBooks...')
    qb_connect = QuickBooksAPIConnection.connect.Connection()
    if qb_connect.status != 200:
        logger.error('Unable to connect to quickbooks, status: ' + str(qb_connect.status))
        exit(1)
    logger.info("Successfully connected to QuickBooks")
    while True:
        for transaction in qb_connect.payed_transactions:
            clerk_ref = qb_connect.payed_transactions[transaction]["Clerk Reference"]
            logger.info('Searching Clerk with reference: ' + clerk_ref)
            status = ClerkAPIConnection.connect.search_id(clerk_ref)
            if int(status) in [0, 1, 3]:
                logger.info('Clerk status is not done -> moving to done: ' + clerk_ref)
                clerk_success = ClerkAPIConnection.connect.update_status(clerk_ref, "2", {'status': 2})
                if clerk_success == 200:
                    logger.info('Successfully changed clerk ref: ' + clerk_ref + " -> to done")
                else:
                    logger.warning('Clerk was not able to be changed to done: ' + clerk_ref)
                jira_success = JiraAPIConnection.connect.update_jira(transaction)
                if jira_success == 204:
                    logger.info('Successfully changed Jira ticket: ' + transaction + " -> to done")
                else:
                    logger.warning('Jira ticket was not able to be changed to done: ' + transaction)
                qb_update_success = qb_connect.update_invoice(qb_connect.payed_transactions[transaction]
                                                              ["QuickBooks Ref"])
                if qb_update_success == 200:
                    logger.info('Successfully changed private memo of quickbooks: ' + transaction + " -> to invoiced")
                else:
                    logger.warning('Was not able to change private memo of quickbooks: ' + transaction)
                print("-------------------------------------------------")
                if clerk_success == 200 and jira_success == 204 and qb_update_success == 200:
                    qb_ref = qb_connect.payed_transactions[transaction]["QuickBooks Ref"]
                    str_reports_arr.append("-------------------------------------------------\n"
                                           "Successfully moved tickets ------>\n"
                                           f"Clerk Reference: {clerk_ref}\nJira Reference: {transaction}\n"
                                           f"QuickBooks ID: {qb_ref}\n"
                                           f"-------------------------------------------------")
                    print("Successfully moved tickets ------>")
                    print(f"""Clerk Reference: " + {clerk_ref}
                    Jira Reference: {transaction}
                    QuickBooks ID: {qb_ref}""")
                    print("------> To Completed")
                print("-------------------------------------------------")
            else:
                logger.warning('Clerk status is already done terminating ticket change: ' + clerk_ref)
        if len(str_reports_arr) != 0:
            logger.info("Changed " + str(len(str_reports_arr)) + " tickets to invoiced.")
            logger.info(str_reports_arr)
        else:
            logger.info("No tickets were changed")

        time.sleep(60 * 55)
        new_access_token, new_refresh_token = qb_connect.refresh_access_token(qb_connect.REFRESH_TOKEN,
                                                                              qb_connect.CLIENT_ID,
                                                                              qb_connect.CLIENT_SECRET)
        qb_connect.run_connection(new_access_token, new_refresh_token)

        