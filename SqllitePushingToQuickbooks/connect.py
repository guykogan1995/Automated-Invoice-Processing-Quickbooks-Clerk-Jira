"""
Author: Kevin Crotteau
"""
import json
import sqlite3
import requests
import xmltodict
import QuickBooksAPIConnection.connect
creds = {}


def parse_post_request(request):

    try:
        # Connect to SQLite database
        conn = sqlite3.connect('Jira-Quickbooks-sql.db')
        cur = conn.cursor()

        # data = json.loads(request)
        data = request.json()
        column = data['key']
        result = cur.execute(f"SELECT * FROM Invoices WHERE jira_id = '{column}'")
        val = result.fetchone()
        if val is not None:
            return "Invoice already exists!"
        # Execute a query to retrieve refreshToken and realmId
        clientId = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_id';").fetchone()[1]
        clientSecret = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_secret';").fetchone()[1]
        refreshToken = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'refresh_token';").fetchone()[1]
        companyCode = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'realm_id';").fetchone()[1]


        # Attempt to refresh the access token
        try:
            accessToken, new_refresh_token = QuickBooksAPIConnection.connect.refresh_access_token(refreshToken, clientId, clientSecret)
             #Update the database with the new token
            cur.execute(f"UPDATE Credentials SET value = '{new_refresh_token}' WHERE identifier = 'refresh_token';")
            cur.execute(f"UPDATE Credentials SET value = '{accessToken}' WHERE identifier = 'authorization_token';")
            conn.commit()
        except Exception as e:
            conn.close()
            raise e  # Re-raise the exception to handle it in the outer try-except block

        # Close the database connection
        conn.close()
        # Extract data from request body
        # data = request.json
        # data = json.loads(request)
        customer_name = data['fields']['customfield_10002'][0]['name']
        qb_url = "https://quickbooks.api.intuit.com"
        # Fetch customer data
        response = requests.get(f"{qb_url}/v3/company/{companyCode}/query?query=SELECT * FROM Customer where DisplayName = '{customer_name}'",
                                headers={'Authorization': f'Bearer {accessToken}',
                                        'Accept': 'application/json'})
        if response.status_code == 200:
            qb_cus_data = response.json()['QueryResponse']['Customer']
            print(qb_cus_data)
        else:
            # add in logic to update db
            print(f"Failed to fetch customers: {response.text}")
            
        # Find customer ID by matching the name
        customer_id = None
        for customer in qb_cus_data:
            if customer['DisplayName'] == customer_name:
                customer_id = customer['Id']
                break

        # Invoice creation logic
        multiLine = [
            "customfield_10146",
            "customfield_10107",
            "customfield_10146",
            "customfield_10144",
            "customfield_10145",
            "customfield_10138",
            "customfield_10101"
        ]  # nested field
        singleLine = [
            "customfield_10119",
            "customfield_10102",
            "customfield_10117"
        ]  # singleLine fields
        DiscountFields = [
            "customfield_10116",
            "customfield_10147"
        ]  # discount fields
        Line = []
        DiscountAmount = 0
        TotalAmount = 0

        for key, val in data['fields'].items():
            if key in multiLine:
                if val is not None:
                    for item in val:
                        description, amount_str = item['value'].rsplit(' - $', 1)
                        amount = float(amount_str)
                        Line.append({
                            "DetailType": "SalesItemLineDetail",
                            "Amount": amount,
                            "SalesItemLineDetail": {"Qty": 1.0},
                            "Description": description
                        })
        
            elif key in singleLine:
                if val is not None:
                    description, amount_str = val['value'].rsplit(' - $', 1)
                    amount = float(amount_str)
                    Line.append({
                        "DetailType": "SalesItemLineDetail",
                        "Amount": amount,
                        "SalesItemLineDetail": {"Qty": 1.0},
                        "Description": description
                    })
        
            elif key in DiscountFields and val is not None:
                DiscountAmount += float(val)
        
        if DiscountAmount > 0:
            Line.append({
                "DetailType": "DiscountLineDetail",
                "Amount": DiscountAmount,
                "DiscountLineDetail": {"PercentBased": False}
            })
        
        invoice_data = {
            "Line": Line,
            "CustomerRef": {"value": customer_id},
            "CustomField":
                [
                    {
                        "DefinitionId": "2",
                        "StringValue": data['fields']['summary'],
                        "Type": "StringType",
                        "Name": "PLAINTIFF/CASE REF"
                    },
                    {
                        "DefinitionId": "3",
                        "StringValue": data['key'],
                        "Type": "StringType",
                        "Name": "CASE ID"
                    }
                ],
        # "DocNumber": {"value": data['key']}
        }


        add_invoice_response = requests.post(f"{qb_url}/v3/company/{companyCode}/invoice",
                                             json=invoice_data,
                                             headers={'Authorization': f'Bearer {accessToken}'})
        
        if add_invoice_response.status_code == 200:
            jira_key = data['key']
            qb_key = xmltodict.parse(add_invoice_response.text)['IntuitResponse']['Invoice']['Id']
            conn = sqlite3.connect('Jira-Quickbooks-sql.db')
            cur = conn.cursor()
            cur.execute(f'INSERT INTO Invoices (jira_id, quickbooks_id) VALUES ("{jira_key}", "{qb_key}")')
            conn.commit()
            return {'success': True, 'data': add_invoice_response}
        else:
            # add in logic to update db
            print(f"Failed to add invoice: {add_invoice_response.text}")
            return {'success': False, 'data': add_invoice_response}

    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return {
            'success': False,
            'error': str(e)
        }
