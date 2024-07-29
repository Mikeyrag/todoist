import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
#import requests
#import json
import openai
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Scopes required by the application
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def chunked(iterable, size):
    """Yield successive chunks from iterable of given size."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

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

#def print_email_snippets(service, messages):
    """Prints the snippets of the provided emails."""
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        print(f"Message snippet: {msg['snippet']}")


def call_chatgpt_api(text):
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-turbo",
            messages=[
                {"role": 
                    "system", 
                 "content": 
                    "Turn the following email into a to-do list task item with the format: 'Task: [task]; Due: [due date] (if applicable); Email Subject: [subject]'."},
                {"role": 
                    "user", 
                "content": 
                    text}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Failed to generate tasks due to an error: {e}"
    

    """ api_url = "https://api.openai.com/v1/engines/davinci/completions"
    headers = {
        'Authorization': MY_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'system', 'content': 'Turn the following email into a task item:'},
                     {'role': 'user', 'content': text}]
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return json.loads(response.text)['choices'][0]['message']['content']
    else:
        return "Failed to generate tasks due to an error" """

def process_emails_to_tasks(messages, service, chunk_size=10):
    """Processes the email messages to extract the tasks."""
    tasks = []
    total_emails = len(messages)
    processed_emails = 0

    for chunk in chunked(messages, chunk_size):
        for message in chunk:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            email_text = msg['snippet']
            task = call_chatgpt_api(email_text)
            print(task)
            tasks.append(task)
            processed_emails += 1
            logging.info(f"Processed {processed_emails} of {total_emails} emails.")
        
        time.sleep(10)
        
    return tasks

def main():
    """Main function to orchestrate the fetching and displaying of Gmail emails."""
    creds = get_credentials()
    service = init_gmail_service(creds)
    messages = fetch_unread_emails(service)
    if messages:
        #print_email_snippets(service, messages)
        tasks = process_emails_to_tasks(messages, service)
        print("Generated Tasks:")
        for task in tasks:
            print(task)

if __name__ == '__main__':
    main()
