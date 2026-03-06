"""
Gmail Authentication Helper

Run this script once to authenticate with Gmail API and create token.json.
Uses credentials.json from the project root.

Usage:
    python gmail_authenticate.py
"""

import os
import sys
from pathlib import Path

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail dependencies not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
TOKEN_FILE = Path.home() / '.gmail' / 'token.json'


def main():
    """Run Gmail OAuth authentication flow."""
    print("=" * 50)
    print("Gmail Authentication for AI Employee")
    print("=" * 50)
    
    # Ensure .gmail directory exists
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for credentials file
    if not CREDENTIALS_FILE.exists():
        print(f"\nError: credentials.json not found at {CREDENTIALS_FILE}")
        print("\nTo get credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials.json")
        print(f"6. Place it at: {CREDENTIALS_FILE}")
        return
    
    print(f"\nCredentials found: {CREDENTIALS_FILE}")
    
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        print(f"Found existing token: {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            if creds and creds.valid:
                print("\n✓ Token is valid. No re-authentication needed.")
                print("\nToken details:")
                print(f"  Client ID: {creds.client_id}")
                print(f"  Scopes: {creds.scopes}")
                return
            elif creds and creds.expired and creds.refresh_token:
                print("\nRefreshing expired token...")
                creds.refresh(Request())
                
                # Save refreshed token
                with open(TOKEN_FILE, 'w') as f:
                    f.write(creds.to_json())
                
                print("✓ Token refreshed successfully!")
                return
            else:
                print("Token invalid. Re-authenticating...")
        except Exception as e:
            print(f"Error loading token: {e}")
    
    # Start OAuth flow
    print("\n" + "=" * 50)
    print("Starting OAuth authentication flow...")
    print("=" * 50)
    print("\nA browser window will open.")
    print("Sign in with your Google account.")
    print("Grant permissions when prompted.")
    print("\nOpening browser in 2 seconds...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        
        print("\n" + "=" * 50)
        print("✓ Authentication successful!")
        print("=" * 50)
        print(f"✓ Token saved to: {TOKEN_FILE}")
        print("\nYou can now run gmail_watcher.py")
        print("\nTest with:")
        print("  python scripts/gmail_watcher.py")
        
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        print("\nTroubleshooting:")
        print("- Ensure credentials.json is valid")
        print("- Check that Gmail API is enabled in Google Cloud Console")
        print("- Try deleting token.json and running again")


if __name__ == '__main__':
    main()
