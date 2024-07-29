import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required by the application
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_credentials():
    """Handles the authentication and returns valid credentials."""
    creds = None
    # Check if the token file exists and load it
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If credentials are invalid or absent, initiate the authorization flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def init_gmail_service(creds):
    """Initializes the Gmail API service."""
    return build('gmail', 'v1', credentials=creds)

def fetch_unread_emails(service):
    """Fetches unread emails from the user's Gmail account."""
    try:
        # Fetch unread emails from the inbox
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
        messages = results.get('messages', [])
        if not messages:
            print('No unread messages found.')
            return []
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return []

def print_email_snippets(service, messages):
    """Prints the snippets of the provided emails."""
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        print(f"Message snippet: {msg['snippet']}")

def main():
    """Main function to orchestrate the fetching and displaying of Gmail emails."""
    creds = get_credentials()
    service = init_gmail_service(creds)
    messages = fetch_unread_emails(service)
    if messages:
        print_email_snippets(service, messages)

if __name__ == '__main__':
    main()
