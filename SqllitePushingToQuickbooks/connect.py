"""
Author: Kevin Crotteau
"""
import json
import sqlite3
import requests
import xmltodict
import QuickBooksAPIConnection.connect
import Test.test
import xml.etree.ElementTree as ET
creds = {}


def parse_post_request(request):
    try:
        print("Connecting to DB for Credentials")
        # Connect to SQLite database
        conn = sqlite3.connect('Jira-Quickbooks-sql.db')
        cur = conn.cursor()
        print("DB connected")
        # Execute a query to retrieve refreshToken and realmId
        clientId = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_id';").fetchone()[1]
        clientSecret = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'client_secret';").fetchone()[1]
        refreshToken = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'refresh_token';").fetchone()[1]
        companyCode = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'realm_id';").fetchone()[1]

        # Attempt to refresh the access token
        try:
            print("refreshing connection")
            accessToken, new_refresh_token = QuickBooksAPIConnection.connect.refresh_access_token(refreshToken, clientId, clientSecret)
            #Update the database with the new token
            cur.execute(f"UPDATE Credentials SET value = '{new_refresh_token}' WHERE identifier = 'refresh_token';")
            cur.execute(f"UPDATE Credentials SET value = '{accessToken}' WHERE identifier = 'authorization_token';")
            conn.commit()
        except Exception as e:
            conn.close()
            raise e  # Re-raise the exception to handle it in the outer try-except block
        
        print("Begin Parsing Request")
        data_key, Lines, customer_name, summary, reporter_email, requester_name = Test.test.extract_info_with_organization(request, companyCode, accessToken)
        
        print("Connecting to DB to check for invoice duplication")
        conn = sqlite3.connect('Jira-Quickbooks-sql.db')
        cur = conn.cursor()
        result = cur.execute(f"SELECT * FROM Invoices WHERE jira_id = '{data_key}'")
        val = result.fetchone()
        if val is not None:
            print(f"Invoice {data_key} already exists")
            return {'success': True, 'data': f"Invoice already exists for {data_key}"}

        # Close the database connection
        conn.close()
        
        qb_url = "https://quickbooks.api.intuit.com"
        # Fetch customer data
        print(f"fetching customer: {customer_name}")
        response = requests.get(f"{qb_url}/v3/company/{companyCode}/query?query=SELECT * FROM Customer where DisplayName = '{customer_name}'",
                                headers={'Authorization': f'Bearer {accessToken}',
                                        'Accept': 'application/json'})
        if response.status_code == 200:
            qb_cus_data = response.json()['QueryResponse']['Customer']
            print(f'Customer found: {qb_cus_data}')
        else:
            # add in logic to update db
            print(f"Failed to fetch customers: {response.text}")
            return {'success': False, 'data': f"Failed to fetch customer, please ensure {customer_name} is in qb and contact Kevin if issue persists"}
            
        # Find customer ID by matching the name
        customer_id = None
        for customer in qb_cus_data:
            if customer['DisplayName'] == customer_name:
                customer_id = customer['Id']
                customer_email = customer['PrimaryEmailAddr']['Address']
                sales_term = customer['SalesTermRef']['value']
                break
        
        if customer_email == 'REQUESTER@EMAIL.COM':
            if reporter_email:
                customer_email = reporter_email
            else:
                print('reporter email is null')

        
        invoice_data = {
            "Line": Lines,
            "CustomerRef": {"value": customer_id},
            "CustomField":
                [
                    {
                        "DefinitionId": "1",
                        "StringValue": requester_name,
                        "Type": "StringType",
                        "Name": "REQUESTER'S NAME"
                    },
                    {
                        "DefinitionId": "2",
                        "StringValue": summary,
                        "Type": "StringType",
                        "Name": "PLAINTIFF/CASE REF"
                    },
                    {
                        "DefinitionId": "3",
                        "StringValue": data_key,
                        "Type": "StringType",
                        "Name": "CASE ID"
                    }
                ],
                "BillEmail": {
                    "Address": customer_email
                },
                # "DocNumber": {"value": data['key']}
        }
        
        print(f"invoice data: {invoice_data}")
        
        if sales_term:
            invoice_data["SalesTermRef"] = {"value": sales_term}

        print("sending invoice")
        add_invoice_response = requests.post(f"{qb_url}/v3/company/{companyCode}/invoice",
                                             json=invoice_data,
                                             headers={'Authorization': f'Bearer {accessToken}'})
        
        if add_invoice_response.status_code == 200:
            print('Invoince sucessfully sent to quickbooks')
            jira_key = data_key
            qb_key = xmltodict.parse(add_invoice_response.text)['IntuitResponse']['Invoice']['Id']
            conn = sqlite3.connect('Jira-Quickbooks-sql.db')
            cur = conn.cursor()
            cur.execute(f'INSERT INTO Invoices (jira_id, quickbooks_id) VALUES ("{jira_key}", "{qb_key}")')
            conn.commit()
            print(f'Added {jira_key} to database')
            link =  get_payment_link(add_invoice_response, companyCode, accessToken)
            return {'success': True, 'data': link}
        else:
            # add in logic to update db
            print(f"Failed to add invoice: {add_invoice_response.text}")
            return {'success': False, 'data': f"Failed to add invoice for {data_key}"}

    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"error in processing {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_payment_link(response, companyCode, access_token):
    response_text = response.text
    
    # Parse the XML content
    root = ET.fromstring(response_text)

    # Define the namespace
    namespace = {'ns': 'http://schema.intuit.com/finance/v3'}


    # Find the first <Id> element within <Invoice>, taking into account the namespace
    invoice_id = root.find('.//ns:Invoice/ns:Id', namespaces=namespace).text

    print("Invoice ID:", invoice_id)

    base_url = 'https://quickbooks.api.intuit.com'

    url =f"{base_url}/v3/company/{companyCode}/invoice/{invoice_id}?minorversion=36&include=invoiceLink"

    auth_header = 'Bearer {0}'.format(access_token)

    headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
            }
    invoice_response = requests.get(url, headers=headers)

    if invoice_response.status_code == 200:
        invoices = invoice_response.json()
        invoice_link = invoices['Invoice']['InvoiceLink']
        print(f'Successfully fetching invoicelink {invoice_link}')
        return invoice_link
    else:
        print(f"Failed to fetch invoice payment link: {invoice_response.text}")
        return None
