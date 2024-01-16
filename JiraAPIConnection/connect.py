import requests
from requests.auth import HTTPBasicAuth
import json


def update_jira(id_to_update):
    id_to_update = "RFR-" + id_to_update
    url = f"https://redfolderresearch.atlassian.net/rest/api/3/issue/{id_to_update}"
    credentials = ""
    auth = HTTPBasicAuth("tech@redfolderresearch.com", credentials)

    headers = {
        "Authorization": "Basic " + credentials,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = json.dumps( { "transition" : {
        "id": "5"
    }})

    response = requests.request(
      "POST",
      url,
      data=payload,
      headers=headers,
      auth=auth
    )
    print(response)


update_jira("45")

