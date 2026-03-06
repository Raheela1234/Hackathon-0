"""
Gmail Watcher Module

Monitors Gmail for new important/unread emails and creates action files
in the Obsidian vault for Qwen Code to process.

Credentials are loaded from credentials.json in the project root.

Usage:
    python gmail_watcher.py /path/to/vault
"""

import os
import sys
import pickle
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError as e:
    GMAIL_AVAILABLE = False
    print(f"Gmail dependencies not installed: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Import base watcher
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new important/unread emails.
    
    When a new email is detected, it:
    1. Fetches the email content
    2. Creates a .md action file in Needs_Action
    3. Tracks the email ID to avoid duplicates
    """
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'emergency', 'invoice', 'payment', 
        'billing', 'help', 'support', 'issue', 'important',
        'client', 'customer', 'order', 'purchase'
    ]
    
    def __init__(self, vault_path: str, credentials_path: str = None, 
                 token_path: str = None, check_interval: int = 120):
        """
        Initialize the Gmail watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail OAuth credentials.json
            token_path: Path to store/load token.json
            check_interval: Seconds between checks (default: 120)
        """
        if not GMAIL_AVAILABLE:
            raise ImportError(
                "Gmail dependencies not installed. Run: "
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        super().__init__(vault_path, check_interval)
        
        # Set default paths - look for credentials.json in project root
        project_root = Path(__file__).parent.parent
        self.credentials_path = Path(credentials_path) if credentials_path else project_root / 'credentials.json'
        self.token_path = Path(token_path) if token_path else Path.home() / '.gmail' / 'token.json'
        
        # Ensure token directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gmail service
        self.service = self._authenticate()
        
        # Load previously processed email IDs
        self.load_processed_ids()
        
        self.logger.info(f"Credentials path: {self.credentials_path}")
        self.logger.info(f"Token path: {self.token_path}")
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        # Import here to avoid issues at module load
        import google.auth.transport.requests
        
        try:
            creds = None

            # Load existing token
            if self.token_path.exists():
                try:
                    creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                    self.logger.info("Loaded existing token")
                except Exception as e:
                    self.logger.warning(f"Could not load token: {e}")
                    creds = None

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token...")
                    try:
                        creds.refresh(google.auth.transport.requests.Request())
                        # Save refreshed token
                        with open(self.token_path, 'w') as f:
                            f.write(creds.to_json())
                        self.logger.info("Token refreshed successfully")
                    except Exception as e:
                        self.logger.warning(f"Token refresh failed: {e}")
                        creds = None

                # Need new auth
                if not creds or not creds.valid:
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Credentials file not found at {self.credentials_path}\n"
                            "Please ensure credentials.json exists in the project root."
                        )
                    
                    self.logger.info("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    
                    # Save token for future use
                    with open(self.token_path, 'w') as f:
                        f.write(creds.to_json())
                    self.logger.info("Authentication successful, token saved")
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail service initialized")
            return service
            
        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f'Authentication failed: {e}')
            raise
    
    def check_for_updates(self) -> list:
        """
        Check Gmail for new important/unread emails.
        
        Returns:
            List of new email message data
        """
        new_emails = []
        
        try:
            # Fetch unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=25
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                msg_id = message['id']
                
                # Skip already processed emails
                if msg_id not in self.processed_ids:
                    # Fetch full message details
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()
                    
                    # Extract headers
                    headers = {h['name']: h['value'] 
                              for h in full_msg['payload']['headers']}
                    
                    new_emails.append({
                        'id': msg_id,
                        'from': headers.get('From', 'Unknown'),
                        'to': headers.get('To', 'Unknown'),
                        'subject': headers.get('Subject', 'No Subject'),
                        'date': headers.get('Date', ''),
                        'snippet': message.get('snippet', '')
                    })
                    
                    self.processed_ids.add(msg_id)
            
            # Save processed IDs
            self.save_processed_ids()
            
        except HttpError as error:
            self.logger.error(f'Gmail API error: {error}')
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
        
        return new_emails
    
    def _get_priority(self, email_data: dict) -> str:
        """Determine email priority based on content."""
        subject = email_data.get('subject', '').lower()
        from_addr = email_data.get('from', '').lower()
        snippet = email_data.get('snippet', '').lower()
        
        # Check for priority keywords
        for keyword in self.PRIORITY_KEYWORDS:
            if keyword in subject or keyword in snippet:
                return 'high'
        
        # Check if from known contact (add your important contacts/domains)
        known_domains = ['@client.com', '@partner.com', '@company.com']
        for domain in known_domains:
            if domain in from_addr:
                return 'high'
        
        return 'medium'
    
    def create_action_file(self, email_data: dict) -> Path:
        """
        Create an action file for the email.
        
        Args:
            email_data: Dict with email details
            
        Returns:
            Path to the created action file
        """
        # Determine priority
        priority = self._get_priority(email_data)
        
        # Create safe filename from subject
        safe_subject = self._safe_filename(email_data['subject'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        content = f'''---
type: email
from: {email_data['from']}
to: {email_data['to']}
subject: {email_data['subject']}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
message_id: {email_data['id']}
---

# Email: {email_data['subject']}

## Sender
**From:** {email_data['from']}

## Received
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Email Preview

{email_data['snippet']}

## Suggested Actions

- [ ] Read full email in Gmail
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

## Notes

<!-- Add any notes about processing this email here -->

---
*Created by Gmail Watcher*
'''
        
        filepath = self.needs_action / f'EMAIL_{email_data["id"]}_{safe_subject}.md'
        filepath.write_text(content, encoding='utf-8')
        
        self.logger.info(f'Created action file for email from {email_data["from"]}')
        
        return filepath
    
    def _safe_filename(self, text: str, max_length: int = 50) -> str:
        """Create a safe filename from text."""
        # Remove invalid characters
        invalid = '<>:"/\\|？*'
        for char in invalid:
            text = text.replace(char, '_')
        
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        
        # Truncate
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def send_email(self, to: str, subject: str, body: str, 
                   in_reply_to: str = None, html: bool = False) -> dict:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            in_reply_to: Message ID to reply to
            html: Whether body is HTML
            
        Returns:
            dict with status and message_id
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message['from'] = 'me'
            
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to
            
            # Add body
            msg_type = 'html' if html else 'plain'
            message.attach(MIMEText(body, msg_type))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Email sent to {to}, message ID: {sent_message['id']}")
            
            return {
                "status": "success",
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId')
            }
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return {"status": "error", "message": str(error)}
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return {"status": "error", "message": str(e)}


def main():
    """Main entry point for running the Gmail watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--credentials', help='Path to credentials.json')
    parser.add_argument('--token', help='Path to token.json')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    try:
        watcher = GmailWatcher(
            vault_path=vault_path,
            credentials_path=args.credentials,
            token_path=args.token,
            check_interval=args.interval
        )
        print(f"Gmail Watcher starting...")
        print(f"Vault: {vault_path}")
        print(f"Check interval: {args.interval}s")
        watcher.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall Gmail dependencies:")
        print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
