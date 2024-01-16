import ClerkAPIConnection.connect
import QuickBooksAPIConnection.connect
import JiraAPIConnection.connect

constants = {
    0: "Draft",
    1: "Sent",
    2: "Paid",
    3: "No Charge"
}

if __name__ == '__main__':
    qb_connect = QuickBooksAPIConnection.connect.Connection("")
    for transaction in qb_connect.payed_transactions:
        clerk_ref = qb_connect.payed_transactions[transaction]["Clerk Reference"]
        print("QuickBooks Clerk Reference: " + clerk_ref)
        status = ClerkAPIConnection.connect.search_id(clerk_ref)
        print("Clerk - Clerk Reference: " + clerk_ref)
        keys_to_exclude = {"export", "exportToConnectedAccounts", "publicLink", "ID", "invoiceTemplate"}
        if int(status) in [0, 1, 3]:
            # update and remove
            ClerkAPIConnection.connect.update_status(clerk_ref, "2", {'status': 2})
            #add to file to not check again when pulling from quickbooks
            #change in jira

