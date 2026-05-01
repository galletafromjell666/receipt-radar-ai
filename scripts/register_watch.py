import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def register_gmail_watch(topic_name):
    """
    Registers a watch on the Gmail mailbox.
    topic_name: The full Pub/Sub topic name, e.g., 'projects/your-project-id/topics/your-topic-name'
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    
    # This call must be repeated at least every 7 days
    result = service.users().watch(userId='me', body=request).execute()
    print(f"Watch registered! Response: {result}")

if __name__ == '__main__':
    # You would get this from your GCP Console
    TOPIC = "projects/your-project-id/topics/your-topic-name"
    register_gmail_watch(TOPIC)
