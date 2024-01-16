import http.client
import json


def search_id(id_search):
    conn = http.client.HTTPSConnection("helloclerk.io")

    headers = {'Accept': "application/json, text/html",
               'Authorization': ''}

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
               'Authorization': ''}

    conn2.request("PATCH", f"/apps/invoices/api/1.0/invoices/{id_search}", payload, headers)
    res = conn2.getresponse()
    data = res.read()
