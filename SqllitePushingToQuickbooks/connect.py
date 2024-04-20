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
import re
creds = {}


def truncate_to_case_number(original_string, max_length):
    """
    Processes the original string based on several conditions:
    - Removes "#N/A" if present.
    - Returns the original string if it's within the max_length limit.
    - Extracts and returns the case number if the string exceeds max_length.
    - If no case number is found but the string is too long, tries to keep the last name.

    Args:
    - original_string (str): The original string to be processed.
    - max_length (int): The maximum length of the string.

    Returns:
    - str: The processed string according to the specified rules.
    """
    # Remove "#N/A" if present, case-insensitively
    refined_string = re.sub(r"#N/A", "", original_string, flags=re.IGNORECASE)
    
    # Check if the refined string is within the maximum length limit
    if len(refined_string) <= max_length:
        return refined_string

    # Attempt to extract the case number
    match = re.search(r"#(\w+)", refined_string)
    if match:
        return match.group(1)

    # If no case number is found and the string is too long,
    # try to truncate the first name and leave the last name.
    words = refined_string.split()
    if len(words) > 1:
        last_name = words[-1]  # Assume the last word is the last name
        # Try to keep as much of the last name as possible
        truncated_last_name = last_name[:max_length] if len(last_name) > max_length else last_name
        return truncated_last_name
    else:
        # If there's only one word, truncate it to the maximum length
        return refined_string[:max_length]


def parse_post_request(request):
    try:
        print("Connecting to DB for Credentials")
        with sqlite3.connect('Jira-Quickbooks-sql.db') as conn:
            cur = conn.cursor()
            # Fetching credentials in a more secure way
            identifiers = ('client_id', 'client_secret', 'refresh_token', 'realm_id')
            placeholders = ', '.join(['?'] * len(identifiers))
            cur.execute(f"SELECT identifier, value FROM Credentials WHERE identifier IN ({placeholders})", identifiers)
            credentials = {row[0]: row[1] for row in cur.fetchall()}
        try:
            print("refreshing connection")
            accessToken, new_refresh_token = QuickBooksAPIConnection.connect.refresh_access_token(
                credentials['refresh_token'], credentials['client_id'], credentials['client_secret'])
             #Update the database with the new token
            cur.execute(f"UPDATE Credentials SET value = '{new_refresh_token}' WHERE identifier = 'refresh_token';")
            cur.execute(f"UPDATE Credentials SET value = '{accessToken}' WHERE identifier = 'authorization_token';")
            conn.commit()
        except Exception as e:
            conn.close()
            raise e  # Re-raise the exception to handle it in the outer try-except block
        print("Begin Parsing Request")
        data_key, Lines, customer_name, summary, reporter_email, requester_name,researcher_name, researcher_two_name, rfr_casenumber = Test.test.extract_info_with_organization(request, credentials['realm_id'], accessToken)
        
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
        response = requests.get(f"{qb_url}/v3/company/{credentials['realm_id']}/query?query=SELECT * FROM Customer where DisplayName = '{customer_name}'",
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
        try:
            case_number = summary.split('#')[1]
        except IndexError:
            case_number = 'No case number present'

        summary = truncate_to_case_number(summary, 30)
        if researcher_two_name is not None:
            researcher_name = f'{researcher_name}, {researcher_two_name}'
        
        invoice_data = {
            "Line": Lines,
            "CustomerRef": {"value": customer_id},
            "CustomField":
                [
                    {
                        "DefinitionId": "1",
                        "StringValue": requester_name.upper(),
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
                "PrivateNote": f"{researcher_name.upper()}",
                "CustomerMemo": {
                    "value": rfr_casenumber
                    },
                "EmailStatus":"NeedToSend",
                "AllowOnlineACHPayment":True,
                "AllowOnlineCreditCardPayment":True,
                # "DocNumber": {"value": data['key']}
        }
        
        print(f"invoice data: {invoice_data}")
        
        if sales_term:
            invoice_data["SalesTermRef"] = {"value": sales_term}

        print("sending invoice")
        add_invoice_response = requests.post(f"{qb_url}/v3/company/{credentials['realm_id']}/invoice",
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
            link =  get_payment_link(add_invoice_response, credentials['realm_id'], accessToken)
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
