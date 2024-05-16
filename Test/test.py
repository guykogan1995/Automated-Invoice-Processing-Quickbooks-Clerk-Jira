import re
import json
import requests

mapping_dict = {
        (25,): {"qb_id": (223,), "description": "Auto Policy Limits"},
        (25,29): {"qb_id": (321,), "description": "Specialty Carrier Auto Policy Limits"},
        (25,32): {"qb_id": (315,), "description": "AAA California Auto Policy Limits"},
        (25,87): {"qb_id": (223,363,), "description": "No-Hit Auto Policy Limits"},
        (26,): {"qb_id": (223,), "description": "Homeowners or Renters Policy Limits"},
        (26,30): {"qb_id": (321,), "description": "Specialty Homeowners or Renters Policy Limits"},
        (26,33): {"qb_id": (315,), "description": "AAA California Homeowners or Renters Policy Limits"},
        (26,88): {"qb_id": (223,363), "description": "No-Hit Homeowners or Renters Policy Limits"},
        (69,): {"qb_id": (223,263), "description": "Umbrella Policy Limits"},
        (69,70): {"qb_id": (321,), "description": "Specialty Carrier Umbrella Policy Limits"},
        (69,71): {"qb_id": (315,), "description": "AAA California Specialty Carrier Umbrella Policy Limits"},
        (28,): {"qb_id": (266,), "description": "International Auto Policy Limits"},
        (28,89): {"qb_id": (00), "description": "No Hit - International Auto Policy Limits"}, #need this one
        (40,): {"qb_id": (225,), "description": "COMMERCIAL POLICY LIMITS"},
        (40,44): {"qb_id": (225,263), "description": "COMMERCIAL POLICY LIMITS"},
        (40,82): {"qb_id": (225,372), "description": "COMMERCIAL POLICY LIMITS"},
        (41,): {"qb_id": (225,), "description": "COMMERCIAL POLICY LIMITS"},
        (41,45): {"qb_id": (225,263), "description": "COMMERCIAL POLICY LIMITS"},
        (41,83): {"qb_id": (225,372), "description": "COMMERCIAL POLICY LIMITS"},
        (46,): {"qb_id": (225,), "description": "COMMERCIAL POLICY LIMITS"},
        (46,47): {"qb_id": (225,263), "description": "COMMERCIAL POLICY LIMITS"},
        (46,85): {"qb_id": (225,372), "description": "COMMERCIAL POLICY LIMITS"},
        (42,): {"qb_id": (278,), "description": ""},
        (42,84): {"qb_id": (278,364), "description": ""},
        (49,): {"qb_id": (229,), "description": "Auto"},
        (49,51): {"qb_id": (368,), "description": "Auto"},
        (49,53): {"qb_id": (316,), "description": "Auto"},
        (49,56): {"qb_id": (229,376,), "description": "Auto"}, ##should remove this
        (49,56,72): {"qb_id": (229,377), "description": "Auto"}, 
        (49,56,73): {"qb_id": (229,376), "description": "Auto"}, 
        (49,58): {"qb_id": (229,378), "description": "Auto"},
        (50,): {"qb_id": (229,), "description": "Homeowners"},
        (50,52): {"qb_id": (368,), "description": "Homeowners"},
        (50,54): {"qb_id": (316,), "description": "Homeowners"},
        (50,57): {"qb_id": (229,376), "description": "Homeowners"},
        (50,57,74): {"qb_id": (229,377), "description": "Homeowners"},
        (50,57,75): {"qb_id": (229,3769), "description": "Homeowners"},
        (50,59): {"qb_id": (229,378), "description": "Homeowners"},
        (61,): {"qb_id": (232,), "description": "Commercial Auto"},
        (61,64): {"qb_id": (232,380), "description": "Commercial Auto"},
        (61,64,78): {"qb_id": (232,381), "description": "Commercial Auto"},
        (61,64,79): {"qb_id": (232,380), "description": "Commercial Auto"},
        (61,67): {"qb_id": (232,379), "description": "Commercial Auto"},
        (60,): {"qb_id": (232,), "description": "Commercial General"},
        (60,63): {"qb_id": (232,380), "description": "Commercial General"},
        (60,63,76): {"qb_id": (232,381), "description": "Commercial General"},
        (60,63,77): {"qb_id": (232,380), "description": "Commercial General"},
        (60,66): {"qb_id": (232,379), "description": "Commercial General"},
        (62,): {"qb_id": (232,), "description": "Commercial Other"},
        (62,65): {"qb_id": (232,380), "description": "Commercial Other"},
        (62,65,80): {"qb_id": (232,381), "description": "Commercial Other"},
        (62,65,81): {"qb_id": (232,380), "description": "Commercial Other"},
        (62,68): {"qb_id": (232,379), "description": "Commercial Other"},
            "DATE OF LOSS 1+ YEARS": {"qb_id": (249,), "description": ""}, 
    "DATE OF LOSS 3+ YEARS": {"qb_id": (250,), "description": ""},
    "DATE OF LOSS 5+ YEARS": {"qb_id": (251,), "description": ""},
    "8 - HOUR RUSH REQUEST - $100.00": {"qb_id": (361,), "description": ""},
    "3 - HOUR RUSH REQUEST - $300.00": {"qb_id": (255,), "description": ""},
    "1 - DAY RUSH REQUEST - $75.00": {"qb_id": (257,), "description": ""},
    "3 - DAY RUSH REQUEST - $50.00": {"qb_id": (248,), "description": ""},
    "5 - DAY RUSH REQUEST - $25.00": {"qb_id": (258,), "description": ""},
    "POLICY NUMBER": {"qb_id": (259,), "description": ""},
    "SKIP TRACE": {"qb_id": (286,), "description": ""},
    "PROPERTY DAMAGE LIMITS": {"qb_id": (261,), "description": ""},
    "POLICY PERIOD": {"qb_id": (260,), "description": ""},
    "UM/UIM LIMITS": {"qb_id": (262,), "description": ""},
    "UMBRELLA POLICY LIMITS": {"qb_id": (263,), "description": "UMBRELLA ADD ON"},
        }

custom_pricing_rules = {
"Kevin Test Company": {
232: 700,
225: 375,
229: 500,
223: 175,
315: 375,
224: 225,
372: -375, #no hit commercial
},
"WILSHIRE LAW FIRM": {
232: 700,
225: 375,
229: 500,
223: 175,
315: 375,
224: 225,
372: -375, #no hit commercial
},
"CALIFORNIA ACCIDENT FIRM":{
225: 375,
},
"CARPENTER & ZUCKERMAN":{
223: 175,
},
"DANIEL STARK INJURY LAWYERS":{
315: 375,
},
"MORGAN & MORGAN":{
224: 250,
}
}


def apply_custom_pricing(lines, organization):
    """
    Applies custom pricing rules to line items for a specific organization.

    Args:
    - lines (list of dictionaries): The line items with their original pricing.
    - organization (str): The name of the client organization.

    Updates the 'Amount' in each applicable line item dictionary in `lines`.
    """
    if organization in custom_pricing_rules:
        for line in lines:
            qb_id_str = line['SalesItemLineDetail']['ItemRef']['value']
            qb_id = int(qb_id_str)  # Convert ID back to integer for matching
            
            if qb_id in custom_pricing_rules[organization]:
                new_price = custom_pricing_rules[organization][qb_id]
                line['Amount'] = str(new_price)  # Update the price, ensure it's a string

def extract_base_items(input_str):
    """
    Extracts JSON strings associated with each BaseItem using regex.

    Args:
    - input_str (str): The multiline string containing the billing items and JSON strings.

    Returns:
    - List of JSON strings.
    """
    # Regex pattern to match "NewKey-BaseItemX" followed by its JSON string
    pattern = r'"NewKey-BaseItem(\d+)":"(\{.*?\}(?=",))'  # Modified to capture the item number
    matches = re.findall(pattern, input_str, re.DOTALL)

    # Return both the item number and the JSON string
    return [(int(match[0]), f'{match[1]}') for match in matches if match[1]]  # Filter out empty matches


def parse_json_and_extract_values(json_str):
    """
    Parses the JSON string to a dictionary and extracts values from lv1 and beyond.

    Args:
    - json_str (str): JSON string.

    Returns:
    - List of values extracted from the JSON.
    """
    parsed_json = json.loads(json_str)
    values = []
    for key in parsed_json:
        if key.startswith("lv") and key != "lv0":
            values.append(parsed_json[key]["value"])
    return values

def get_qb_id(values):
    """
    Retrieves the QB IDs and description based on the combination of values.

    Args:
    - values (list): List of values extracted from the JSON.

    Returns:
    - A dictionary containing the QB IDs, description, and a placeholder for item prices.
    """
    values_tuple = tuple(sorted(values))
    if values_tuple in mapping_dict:
        qb_id_info = mapping_dict[values_tuple].copy()  # Copy to avoid mutating the original mapping
        qb_id_info["item_price"] = ()  # Placeholder for prices
        return qb_id_info
    else:
        return None

def query_quickbooks_api(client_id, auth_token, qb_ids):
    """
    Queries the QuickBooks API for items based on their IDs and retrieves their Name, ID, and UnitPrice.

    Args:
    - client_id (str): The client ID for the QuickBooks API.
    - auth_token (str): The authentication token.
    - qb_ids (list): List of QB IDs to query.

    Returns:
    - A dictionary with QB IDs as keys and their Name, ID, and UnitPrice as values.
    """
    #tuple breaks the api if singular
    if len(qb_ids) == 1:
        qb_ids = (f"('{qb_ids[0]}')")

    print(f"ids {qb_ids}")
    base_url = 'https://quickbooks.api.intuit.com'

    url = f"{base_url}/v3/company/{client_id}/query?query=select Name, Id, UnitPrice from Item WHERE Id IN {qb_ids}&minorversion=70"

    headers = {'Authorization': f'Bearer {auth_token}','Accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        items_info = response.json()
        qb_items = {item['Id']: {"Name": item['Name'], "UnitPrice": item['UnitPrice']} for item in items_info['QueryResponse']['Item']}
        print(f"succesfully fetched items: {qb_items}")
        # processing response to return id and item
        return qb_items
    else:
        print(f"failed to fetch items: {response}")
        return {}




def update_qb_id_info_with_unit_price(qb_ids_info, qb_items_info):
    """
    Updates the qb_id_info dictionaries with UnitPrice from the QuickBooks API response.

    Args:
    - qb_ids_info (list): A list of dictionaries, each containing qb_id_info including the QB IDs.
    - qb_items_info (dict): A dictionary with QB IDs as keys and their Name, ID, and UnitPrice as values.

    Returns:
    - The updated list of dictionaries with 'item_price' added to each qb_id_info based on matching QB ID.
     """

    for info in qb_ids_info:
        # Check if the QB ID is a tuple (indicating multiple IDs) or a single ID
        if isinstance(info['qb_id'], tuple):
            # Initialize a list to hold the UnitPrices for the matching IDs
            info['item_price'] = []
            # Iterate over each ID in the tuple
            for qb_id in info['qb_id']:
                # Convert ID to str for matching, as keys in qb_items_info are strings
                str_qb_id = str(qb_id)
                if str_qb_id in qb_items_info:
                    # Append the UnitPrice to the item_price list
                    info['item_price'].append(qb_items_info[str_qb_id]['UnitPrice'])
            # Convert the list to a tuple to keep the data immutable
            info['item_price'] = tuple(info['item_price'])
        else:
            # Handle the case for a single QB ID (not demonstrated in the updated requirements)
            str_qb_id = str(info['qb_id'])
            if str_qb_id in qb_items_info:
                info['item_price'] = qb_items_info[str_qb_id]['UnitPrice']

    return qb_ids_info

def extract_info_with_organization(payload, realm_id, new_access_token):
    Lines = []
    organization = ''
    summary = ""
    reporter_email = None
    total_discount = 0
    DOL = None  
    requester_name = None

    # Extract 'key' value
    key_match = re.search(r'"NewKey-key":\s*"([^"]+)"', payload)
    data_key = key_match.group(1) if key_match else None

    # Extract organization name
    organization_match = re.search(r'"NewKey-Organization":"[^{]*\{[^,]*, name=\'([^\']+)\'', payload)
    if organization_match:
        organization = organization_match.group(1)

    # Extract summary
    summary_match = re.search(r'"NewKey-Summary":"([^"]+)"', payload)
    if summary_match:
        summary = summary_match.group(1)

    rfr_casenumber_match = re.search(r'"NewKey-CaseNumber":"([^"]+)"', payload)
    if rfr_casenumber_match:
        rfr_casenumber = rfr_casenumber_match.group(1)
    else:
        rfr_casenumber = 'No Case Number Set'

    # Extract Assignee Email
    assignee_match = re.search(r'"NewKey-Assignee":\s*"([^"]*)"', payload)
    if assignee_match:
        reporter_email = assignee_match.group(1) if assignee_match.group(1) else None

    # Extract DOL
    DOL_match = re.search(r'"NewKey-DOL":"([^"]+)"', payload)
    if DOL_match:
        DOL = DOL_match.group(1)

    # Extract Requester Name
    requester_match = re.search(r'"NewKey-Requester":"([^"]+)"', payload)
    if requester_match:
        requester_name = requester_match.group(1)
    
    # Extract umbrella
    umbrella_match = re.search(r'"NewKey-Umbrella":"([^"]+)"', payload)
    if umbrella_match:
        umbrella = umbrella_match.group(1)
    
    # Search for "NewKey-Researcher" and extract the name
    researcher_match = re.search(r'"NewKey-Researcher":"([^"]+)"', payload)
    researcher_name = researcher_match.group(1) if researcher_match else None
    
    # Search for "NewKey-ResearcherTwo" and extract the name
    researcher_two_match = re.search(r'"NewKey-ResearcherTwo":"([^"]+)"', payload)
    researcher_two_name = researcher_two_match.group(1) if researcher_two_match else None


    # Extract and handle NewKey-discount
    discount_match = re.search(r'"NewKey-discount":\s*"([\d\.]+)"', payload)
    if discount_match:
        Lines.append({
            "DetailType": "DiscountLineDetail",
            "Amount": discount_match.group(1),
            "Description": "Discount",
            "DiscountLineDetail": {"PercentBased": False}
            })
    print('parsing line items')
    qb_ids_to_query=[]
    # This is where the updated logic for the Base items can go
    base_items_data = extract_base_items(payload)  
    for index, base_item_json in enumerate(base_items_data, start=1):  # Start indexing from 1
        values = parse_json_and_extract_values(base_item_json[1])
        qb_id_info = get_qb_id(values)
        if qb_id_info and qb_id_info != 'None':
            if 0 <= base_item_json[0] <= 3:
                if (qb_id_info['qb_id'] == (225,263)) or (qb_id_info['qb_id'] ==  (223,263)):
                    if umbrella == 'Unable to Verify':
                        qb_ids_to_query.append({"qb_id": (273,), "description": "UNABLE TO VERIFY CREDIT"}) #add on discount
            # Check if it's the 4th, 5th, or 6th item since these are Upsells
            if 4 <= base_item_json[0] <= 6:
                qb_id_info['description'] = "Additional Policy Found: " + qb_id_info['description']
                if (qb_id_info['qb_id'] == (225,263)) or (qb_id_info['qb_id'] ==  (223,263)):
                    qb_id_info['qb_id'] == (263,)
                if qb_id_info['qb_id'] == (263,):
                    qb_id_info['description'] = "UMBRELLA POLICY"
            qb_ids_to_query.append(qb_id_info)

    print('parsing dol')
    # Process additional NewKey- fields with conditional logic for 'dateofloss'
    new_fields = ['expedited', 'dateofloss', 'expeditedpl']
    for field in new_fields:
        field_content_match = re.search(rf'"NewKey-{field}":"([^"]*?)"', payload)
        if field_content_match:
            item_name = field_content_match.group(1)
            if item_name in mapping_dict:
                qb_id = mapping_dict[item_name]
                if field == 'dateofloss' and DOL:
                    qb_id['description'] = f"Date of Loss: {DOL}"
                qb_ids_to_query.append(qb_id)  # Collect QB ID for querying

    print('parsing add ons')
    # Process add on fields
    addonservices_match = re.search(r'"NewKey-Addonservices":\s*"([^"]+)"', payload)
    if addonservices_match:
        services = addonservices_match.group(1).split(", ")
        for service in services:
            if service:  # Check if the service is not empty
                text, dollar_value = service.rsplit(' - $', 1)
                if text in mapping_dict:
                    qb_id = mapping_dict[text]
                    print(f'ttesetestsetse - {qb_id}')
                    if umbrella == 'Unable to Verify' and qb_id == {'qb_id': (263,), 'description': 'UMBRELLA ADD ON'}:
                        qb_ids_to_query.append(qb_id)
                        qb_ids_to_query.append({"qb_id": (273,), "description": "UNABLE TO VERIFY CREDIT"}) #add on discoun
                    else:
                        qb_ids_to_query.append(qb_id)  # Collect QB ID for querying
                    

    qb_id_list = tuple(set(
        str(qb_id)  # Convert each QB ID to string to ensure consistency
        for item in qb_ids_to_query
        for qb_id in (item['qb_id'] if isinstance(item['qb_id'], tuple) else (item['qb_id'],))  # Handle both tuple and single ID
    ))

    qb_items_info = query_quickbooks_api(realm_id, new_access_token, qb_id_list)

    qb_ids_info_updated = update_qb_id_info_with_unit_price(qb_ids_to_query, qb_items_info)



    print(f'{qb_ids_to_query}')
    
    for qb_info in qb_ids_to_query:
        if isinstance(qb_info['qb_id'], tuple) and len(qb_info['qb_id']) > 1:
            # Handle cases with multiple QB IDs
            for idx, qb_id in enumerate(qb_info['qb_id']):
                Lines.append({
                    "Amount": str(qb_info['item_price'][idx]),  # Use the corresponding price for each QB ID
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {"ItemRef": {"value": str(qb_id)}, "Qty": 1.0},
                    "Description": qb_info['description'].upper()  # Or use a more suitable description as needed
                    })
        else:
            # Handle the case with a single QB ID or when qb_id is not a tuple
            single_qb_id = qb_info['qb_id'][0] if isinstance(qb_info['qb_id'], tuple) else qb_info['qb_id']
            single_item_price = qb_info['item_price'][0] if isinstance(qb_info['item_price'], tuple) else qb_info['item_price']
            Lines.append({
                "Amount": str(single_item_price),
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {"ItemRef": {"value": str(single_qb_id)}, "Qty": 1.0},
                "Description": qb_info['description'].upper()  # Or use a more suitable description as needed
                })

    
    apply_custom_pricing(Lines, organization)
    
    print(Lines)

    return data_key, Lines, organization, summary, reporter_email, requester_name, researcher_name, researcher_two_name, rfr_casenumber
            
