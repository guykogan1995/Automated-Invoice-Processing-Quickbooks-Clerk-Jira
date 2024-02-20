"""
File: connect.py
Author: Guy Kogan
Date: 1/15/2024
Description: This Python script connects to Jira and changes the tickets
    to Invoice complete after Clerk has been processed.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import sqlite3


def update_jira(id_to_update):
    """
    This function updates Jira tickets to Invoice complete

    :param id_to_update: The Jira ID to update
    :return: the response status code 204 is ticket was successfully updated
    """

    url = f"https://redfolderresearch.atlassian.net/rest/api/3/issue/{id_to_update}/transitions"
    con = sqlite3.connect("Jira-Quickbooks-sql.db")
    cur = con.cursor()
    res = cur.execute("SELECT identifier, value FROM Credentials WHERE identifier = 'jira_cred';")
    jira_id = res.fetchone()[1]
    auth = HTTPBasicAuth("tech@redfolderresearch.com", jira_id)
    con.close()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps({"transition": {
        "id": "431"
    }})

    response = requests.request(
      "POST",
      url,
      data=payload,
      headers=headers,
      auth=auth
    )
    return response.status_code
