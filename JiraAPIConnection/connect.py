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


def update_jira(id_to_update):
    """
    This function updates Jira tickets to Invoice complete

    :param id_to_update: The Jira ID to update
    :return: the response status code 204 is ticket was successfully updated
    """

    url = f"https://redfolderresearch.atlassian.net/rest/api/3/issue/{id_to_update}/transitions"
    with open("Credentials.txt", "r") as f:
        lines = f.readlines()
        credentials = ""
        for line in lines:
            if "CREDENTIALS" in line:
                credentials = line.split()[1]
                break
    auth = HTTPBasicAuth("tech@redfolderresearch.com", credentials)

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
