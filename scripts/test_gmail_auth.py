"""
Quick Gmail Auth Test

Run this to authenticate with Gmail.
A browser will open - sign in and grant permissions.
"""

import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Paths
CREDENTIALS_FILE = Path(__file__).parent.parent / 'credentials.json'
TOKEN_FILE = Path.home() / '.gmail' / 'token.json'

print("=" * 60)
print("Gmail Authentication")
print("=" * 60)
print(f"\nCredentials: {CREDENTIALS_FILE}")
print(f"Token will be saved to: {TOKEN_FILE}")

# Ensure directory exists
TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

# Create OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

print("\nOpening browser for authentication...")
print("Please sign in with your Google account and grant permissions.")
print("\nIf browser doesn't open, copy and paste the URL from the console.")

# Run OAuth server
creds = flow.run_local_server(port=8080, open_browser=True)

# Save token
with open(TOKEN_FILE, 'w') as f:
    f.write(creds.to_json())

print("\n" + "=" * 60)
print("SUCCESS! Authentication complete.")
print(f"Token saved to: {TOKEN_FILE}")
print("=" * 60)

print("\nYou can now run the Gmail Watcher:")
print("  python scripts/gmail_watcher.py")
