"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to the Clerk API and changes
    orders to complete if they are done in Quickbooks.
"""

import http.client
import json


def search_id(id_search):
    """
    This function is used to search and update the ticket for Clerk

    :param id_search: The ticket number to be updated
    :return: the status code of the request should be 200 on success.
    """
    with open("Credentials.txt", "r") as f:
        lines = f.readlines()
        credentials = "JWT "
        for line in lines:
            if "AUTHOR-KEY" in line:
                credentials += line.split()[1]
    conn = http.client.HTTPSConnection("helloclerk.io")
    headers = {'Accept': "application/json, text/html",
               'Authorization': 'JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOjE1MjYsImlhdCI6MTcwMTQ1MjgyMCwianRpIjozNiwidHlwZSI6IkNsZXJrIFN0YXRpYyBUb2tlbiJ9.PVZlj7hPhmKtfbUsMkInGOiePsmBTKBQza3Y9swvpt0'}

    conn.request("GET", f"/apps/invoices/api/1.0/invoices/{id_search}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode("utf-8"))
    stat = json_data["status"]
    print(f"Successfully searched Clerk for received status({stat})")
    return stat


def update_status(id_search, status, json_data):
    conn2 = http.client.HTTPSConnection("helloclerk.io")
    payload = json_data
    payload["status"] = int(status)
    payload = json.dumps(payload).encode('utf-8')
    headers = {'Request-Type': "Regular",
               'Content-Type': "application/json",
               'Accept': "application/json, text/html",
               'Authorization': 'JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.'
                                'eyJpc3MiOjE1MjYsImlhdCI6MTcwMTQ1MjgyMCwian'
                                'RpIjozNiwidHlwZSI6IkNsZXJrIFN0YXRpYyBUb2tlb'
                                'iJ9.PVZlj7hPhmKtfbUsMkInGOiePsmBTKBQza3Y9swvpt0'}
    conn2.request("PATCH", f"/apps/invoices/api/1.0/invoices/{id_search}", payload, headers)
    res = conn2.getresponse()
    return res.status
