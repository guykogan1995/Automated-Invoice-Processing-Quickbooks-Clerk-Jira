import requests
from requests.auth import HTTPBasicAuth
import json


CONFIG_BC = {
  "Policy Existence - Auto Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid": "804e309a-6274-403f-9012-c0d0ed291118",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
        },
    "Results":{
      "formTemplateid": "59acee57-bf2e-4814-a99b-4b7ee04749a5",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":438,
        "Defendant:":439,
        "Insurance:":440,
        "Policy Number:":443,
        "Liability Limits:":{
          "1":425,
          "2":427,
          "3":428
        },
        "Note:":{
          "1":406,
          "2":408,
          "3":410
        }
      }
    }
  },
  "Policy Existence - Commercial Auto Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid":"ed220025-7674-47fb-ab5f-acaba38f1c06",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
    },
    "Results":{
      "formTemplateid":"f95933a0-a95f-40ea-b509-d42109c84f68",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":426,
        "Defendant:":427,
        "Insurance:":430,
        "Policy Number:":429,
        "Liability Limits:":{
          "1":420,
          "3":422
        },
        "Note:":{
          "1":406,
          "3":408
        }
      }
    }
  },
  "Policy Existence - Homeowner's Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid": "7790251e-fcf4-4474-adc6-86969c1c8c7f",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
    },
    "Results":{
      "formTemplateid": "b791c4f3-2d82-403b-b6bb-896c635e6093",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":431,
        "Defendant:":432,
        "Insurance:":434,
        "Policy Number:":435,
        "Liability Limits:":{
          "1":423,
          "2":426,
          "3":427
        },
        "Note:":{
          "1":406,
          "2":408,
          "3":410
        }
      }
    }
  }
}

CONFIG_BASIC = {
  "Policy Existence - Auto Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid": "3ff929f5-e396-4404-8b4e-9e9ff967beff",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
        },
    "Results":{
      "formTemplateid": "8dcbb1d5-ff4b-4985-8aaf-a2eb832917e1",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":435,
        "Defendant:":436,
        "Insurance:":438,
        "Policy Number:":439,
        "Liability Limits:":{
          "1":428,
          "2":430,
          "3":431
        },
        "Note:":{
          "1":406,
          "2":408,
          "3":410
        }
      }
    }
  },
  "Policy Existence - Commercial Auto Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid":"3da8b364-719e-4733-85c6-302febccb0b3",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
    },
    "Results":{
      "formTemplateid":"ecdb7531-7d17-421d-9c73-9a3daf6550a1",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":423,
        "Defendant:":424,
        "Insurance:":426,
        "Policy Number:":427,
        "Liability Limits:":{
          "1":418,
          "3":419
        },
        "Note:":{
          "1":406,
          "3":408
        }
      }
    }
  },
  "Policy Existence - Homeowner's Checklist (A-Day)":{
    "Checklist": {
      "formTemplateid": "4e477509-9045-4101-b73a-9f383c23220a",
      "label":["Date of Loss:", "Defendant:", "Insurance:", "Policy Number:", "Liability Limits:", "Note:"]
    },
    "Results":{
      "formTemplateid": "f50fb8c0-31ea-4dca-b24e-0e33c88a38d2",
      "choiceKey":{
        "fieldKey": "key-choice",
        "field":"choice"
      },
      "answermapping":{
        "Date of Loss:":430,
        "Defendant:":431,
        "Insurance:":433,
        "Policy Number:":434,
        "Liability Limits:":{
          "1":423,
          "2":425,
          "3":426
        },
        "Note:":{
          "1":406,
          "2":408,
          "3":410
        }
      }
    }
  }
}


def fetch_attached_forms(issue_id, cloud_id, auth):
    """
    Fetches all forms attached to a given issue and filters them based on the config.

    Args:
    issue_id (str): The Jira issue ID or key.
    cloud_id (str): The Jira Cloud ID.
    config (dict): Configuration containing the names of the forms to look for.

    Returns:
    list: A list of forms that match the criteria specified in the config.
    """
    url = f"https://api.atlassian.com/jira/forms/cloud/{cloud_id}/issue/{issue_id}/form"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ExperimentalApi": "opt-in"
    }

    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
        forms = response.json()
        return forms

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []


def validate_results_form(attached_forms, config):
    """
    Validates whether the corresponding results forms are attached based on the configuration.
    This function now also retrieves and returns both the template ID and the actual form ID of the results forms.
    
    Args:
    attached_forms (list): A list of all forms attached to the issue.
    config (dict): Configuration that includes mapping of checklist forms to their corresponding results forms.
    
    Returns:
    list: A list of tuples with each tuple containing the checklist form, results template ID, and actual results form ID.
    """
    valid_forms = []
    checklist_forms = [form for form in attached_forms if form['name'].strip() in config]
    
    # Iterate over only checklist forms and check for corresponding results forms
    for form in checklist_forms:
        checklist_name = form['name'].strip()
        checklist_info = config.get(checklist_name, {})
        results_template_id = checklist_info.get('Results', {}).get('formTemplateid', '')
        
        # Find the results form that matches the results template id and capture its actual form ID
        for result_form in attached_forms:
            if result_form['formTemplate']['id'] == results_template_id:
                # Store both the results template ID and the actual form ID
                valid_forms.append((form, results_template_id, result_form['id']))
                break
        else:
            print(f"No corresponding results form found for {checklist_name}")
    
    return valid_forms


def fetch_form_answers(issue_id, form_id, cloud_id, config, checklist_name, auth):
    """
    Fetches answers from a form based on the form ID, issue ID, and cloud ID.

    Args:
    issue_id (str): The Jira issue ID or key.
    form_id (str): The form ID from which to fetch answers.
    cloud_id (str): The Jira Cloud ID.
    config (dict): Configuration dictionary that includes labels for the form answers of interest.
    checklist_name (str): The name of the checklist form for which answers are being fetched.

    Returns:
    dict: A dictionary containing the answers of interest based on the configuration.
    """
    url = f"https://api.atlassian.com/jira/forms/cloud/{cloud_id}/issue/{issue_id}/form/{form_id}/format/answers"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ExperimentalApi": "opt-in"
    }

    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
        answers = response.json()

        # Filter answers based on the labels specified in the config for the checklist form
        labels_of_interest = config[checklist_name]['Checklist']['label']
        filtered_answers = {answer['label'].strip(): answer['answer']
        for answer in answers if any(answer['label'].strip().startswith(label) for label in labels_of_interest)}

        return filtered_answers

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}

def construct_results_payload(answers, choice_value, config, checklist_name):
    """
    Prepares the JSON payload for updating the results form based on the fetched answers and the configuration,
    including handling different field types such as text and paragraph.
    
    Args:
    answers (dict): A dictionary containing the answers fetched from a checklist form.
    choice_value (str): The choice value from the results form to determine specific mappings.
    config (dict): Configuration dictionary that includes mappings for updating the results forms.
    checklist_name (str): The name of the checklist form to get the specific mapping config.
    
    Returns:
    dict: A dictionary containing the payload to update the results form.
    """
    results_config = config[checklist_name]['Results']['answermapping']
    update_payload = {"answers": {}}
    
    for label, answer in answers.items():
        if label in results_config:
            # Handle if the mapping is a dictionary (conditional based on choice)
            if isinstance(results_config[label], dict):
                field_id = results_config[label].get(choice_value)
            else:
                field_id = results_config[label]
            print(label)
            if label == "Note:":
                # Construct paragraph formatted payload
                paragraph_payload = {
                    "adf": {
                        "content": [
                            {
                                "content": [
                                    {"text": answer, "type": "text"}
                                ],
                                "type": "paragraph"
                            }
                        ],
                        "type": "doc",
                        "version": 1
                    }
                }
                update_payload['answers'][str(field_id)] = paragraph_payload
            else:
                # Default text field format
                update_payload['answers'][str(field_id)] = {"text": answer}
    
    return update_payload



def fetch_choice_value(issue_id, results_form_id, cloud_id, config, checklist_name, auth):
    """
    Fetches the choice value from a results form based on a specified fieldKey.
    
    Args:
    issue_id (str): The Jira issue ID or key.
    results_form_id (str): The results form ID to fetch the choice value from.
    cloud_id (str): The Jira Cloud ID.
    config (dict): Configuration dictionary that includes the fieldKey information.
    checklist_name (str): The name of the checklist form to determine which results form to look up.
    
    Returns:
    str: The choice value obtained from the results form.
    """
    field_key = config[checklist_name]['Results']['choiceKey']['fieldKey']
    choice_field = config[checklist_name]['Results']['choiceKey']['field']

    url = f"https://api.atlassian.com/jira/forms/cloud/{cloud_id}/issue/{issue_id}/form/{results_form_id}/format/answers"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ExperimentalApi": "opt-in"
    }
    
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
        answers = response.json()
        print(f'answers: {answers}')
        # Find the answer entry that has the matching fieldKey
        for answer in answers:
            if answer.get('fieldKey') == field_key:
                return answer.get(choice_field, "")
                
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return ""

def update_results_form(issue_id, form_id, cloud_id, payload, auth):
    """
    Sends a POST request to update the results form with the given payload.
    
    Args:
    issue_id (str): The Jira issue ID or key.
    form_id (str): The form ID of the results form to be updated.
    cloud_id (str): The Jira Cloud ID.
    payload (dict): The payload containing the updates to be made to the form.
    
    Returns:
    dict: The response from the server after attempting to update the form.
    """
    url = f"https://api.atlassian.com/jira/forms/cloud/{cloud_id}/issue/{issue_id}/form/{form_id}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ExperimentalApi": "opt-in"
    }
    payload = json.dumps(payload)
    
    try:
        response = requests.request(
           "PUT",
           url,
           data=payload,
           headers=headers,
           auth=auth
        )
        response.raise_for_status()  # Check for HTTP request errors
        return response.json()  # Return the JSON response from the server
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}


def process_forms(issue_id, cloud_id, config, auth):
    """
    Processes each valid checklist form by fetching answers, fetching choice values, constructing payloads,
    and potentially updating results.

    Args:
    issue_id (str): The Jira issue ID or key.
    cloud_id (str): The Jira Cloud ID.
    valid_forms (list): A list of tuples with checklist forms and their corresponding results form template IDs.
    config (dict): Configuration dictionary for the entire process.

    Returns:
    dict: A dictionary with the checklist name as key and the payloads for updating as values.
    """
    all_payloads = {}

    #fetch forms associated with an issue
    forms = fetch_attached_forms(issue_id, cloud_id, auth)
    #grab all the valid forms
    valid_forms = validate_results_form(forms, config)

    for checklist_form, results_template_id, results_form_id in valid_forms:
        form_id = checklist_form['id']
        checklist_name = checklist_form['name'].strip()

        # Fetch choice value dynamically from the results form
        choice_value = fetch_choice_value(issue_id, results_form_id, cloud_id, config, checklist_name, auth)

        # Fetch answers for each valid form
        answers = fetch_form_answers(issue_id, form_id, cloud_id, config, checklist_name, auth)

        # Construct payload for updating results form
        payload = construct_results_payload(answers, choice_value, config, checklist_name)
        all_payloads[results_form_id] = payload

    # Assuming payloads is a dictionary with form IDs as keys and payloads as values
    for results_form_id, data in all_payloads.items():
        payload = data  # The payload to update the form
        response = update_results_form(issue_id, results_form_id, cloud_id, payload, auth)
        print(f"Update response for {checklist_name}: {response}")

    return response

