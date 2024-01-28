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


if __name__ == '__main__':
    qb_connect = QuickBooksAPIConnection.connect.Connection()
    while True:
        for transaction in qb_connect.payed_transactions:
            clerk_ref = qb_connect.payed_transactions[transaction]["Clerk Reference"]
            status = ClerkAPIConnection.connect.search_id(clerk_ref)
            keys_to_exclude = {"export", "exportToConnectedAccounts", "publicLink", "ID", "invoiceTemplate"}
            if int(status) in [0, 1, 3]:
                clerk_success = ClerkAPIConnection.connect.update_status(clerk_ref, "2", {'status': 2})
                jira_success = JiraAPIConnection.connect.update_jira(transaction)
                qb_update_success = qb_connect.update_invoice(qb_connect.payed_transactions[transaction]
                                                              ["QuickBooks Ref"])
                print("-------------------------------------------------")
                if clerk_success == 200 and jira_success == 204 and qb_update_success == 200:
                    print("Successfully moved tickets ------>")
                    print(f"""Clerk Reference: " + {clerk_ref}
                    Jira Reference: {transaction}
                    QuickBooks ID: {qb_connect.payed_transactions[transaction]["QuickBooks Ref"]}""")
                    print("------> To Completed")
                print("-------------------------------------------------")
        time.sleep(60 * 55)
        new_access_token, new_refresh_token = qb_connect.refresh_access_token(qb_connect.REFRESH_TOKEN,
                                                                              qb_connect.CLIENT_ID,
                                                                              qb_connect.CLIENT_SECRET)
        qb_connect.run_connection(new_access_token, new_refresh_token)

        