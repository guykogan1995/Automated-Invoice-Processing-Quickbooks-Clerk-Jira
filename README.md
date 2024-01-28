# Automated Invoice Processing Workflow

## Overview

This Python script automates the workflow for processing invoices by seamlessly connecting to the Clerk API, Jira, and QuickBooks. The script efficiently checks for paid orders in QuickBooks, retrieves corresponding references from Clerk and Jira, and updates the status of tickets to completion.

## Files

1. **main.py**
   - Main script file containing the automation logic.
   - Divided into three sections, each connecting to Clerk API, Jira, and QuickBooks.
   - The script continuously checks for paid transactions and updates related tickets.

2. **Credentials.txt**
   - Text file containing API credentials and authentication details.
   - Separate sections for QuickBooks, Clerk, and Jira credentials.
   - Must be filled out with the appropriate information before running the script.

## Usage

1. **Fill out Credentials.txt:**
   - Open the `Credentials.txt` file and fill in the required information for QuickBooks, Clerk, and Jira.
   - QuickBooks credentials include `CLIENT_ID`, `CLIENT_SECRET`, `REALM_ID`, and `AUTHORIZATION`.
   - Clerk credentials include `AUTHOR-KEY`.
   - Jira credentials include `CREDENTIALS`.

2. **Run the Script:**
   - Navigate to the project directory.
   - Execute the `main.py` script using a Python interpreter.

```bash
python main.py
```

3. **Monitoring:**
   - The script continuously monitors for paid transactions in QuickBooks.
   - If a paid transaction is found, it updates the status in Clerk and Jira.

4. **Refresh Tokens:**
   - The script handles token refreshing for QuickBooks automatically.

## Dependencies

- Python 3.x
- Required Python packages are listed in the script:
  - `http.client`
  - `json`
  - `requests`
  - `intuitlib`

## Important Notes

- Ensure that the `Credentials.txt` file is correctly filled out with the required credentials before running the script.
- This script assumes a continuous monitoring setup, but adjustments can be made based on specific use cases.

## Author

- **Author:** Guy Kogan
- **Date:** 1/15/2024

## License

This project is licensed under the [MIT License](LICENSE.md).

Feel free to customize this README according to your project's specific details and requirements.
