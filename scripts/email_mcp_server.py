"""
Email MCP Server

Model Context Protocol (MCP) server for Gmail operations.
Provides tools for Qwen Code to send, draft, and search emails.

Usage:
    python email_mcp_server.py

Or with custom port:
    python email_mcp_server.py --port 8809
"""

import os
import sys
import json
import logging
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not available. Install with: pip install mcp")


class EmailMCPServer:
    """MCP Server for Gmail operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send',
              'https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """Initialize the Email MCP server."""
        self.credentials_path = Path(credentials_path) if credentials_path else Path.home() / '.gmail' / 'credentials.json'
        self.token_path = Path(token_path) if token_path else Path.home() / '.gmail' / 'token.json'
        
        # Dry run mode
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('EmailMCP')
        
        # Initialize Gmail service
        self.service = None
        if GMAIL_AVAILABLE:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        try:
            creds = None
            
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(google.auth.transport.requests.Request())
                else:
                    if not self.credentials_path.exists():
                        self.logger.error(f"Credentials not found: {self.credentials_path}")
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                with open(self.token_path, 'w') as f:
                    f.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail authentication successful")
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
    
    def send_email(self, to: str, subject: str, body: str, 
                   attachments: list = None, html: bool = False) -> dict:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: List of file paths to attach
            html: Whether body is HTML
            
        Returns:
            dict with status and message_id
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would send email to {to}")
            return {"status": "dry_run", "message": "Email not sent (dry run mode)"}
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message['from'] = 'me'
            
            # Add body
            msg_type = 'html' if html else 'plain'
            message.attach(MIMEText(body, msg_type))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{Path(file_path).name}"'
                            )
                            message.attach(part)
                    except Exception as e:
                        self.logger.warning(f"Could not attach {file_path}: {e}")
            
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
    
    def create_draft(self, to: str, subject: str, body: str, 
                     attachments: list = None, html: bool = False) -> dict:
        """
        Create a draft email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: List of file paths to attach
            html: Whether body is HTML
            
        Returns:
            dict with status and draft_id
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message['from'] = 'me'
            
            # Add body
            msg_type = 'html' if html else 'plain'
            message.attach(MIMEText(body, msg_type))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{Path(file_path).name}"'
                            )
                            message.attach(part)
                    except Exception as e:
                        self.logger.warning(f"Could not attach {file_path}: {e}")
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            self.logger.info(f"Draft created, ID: {draft['id']}")
            
            return {
                "status": "success",
                "draft_id": draft['id'],
                "message": "Draft created. Review and send manually or via approval workflow."
            }
            
        except Exception as e:
            self.logger.error(f"Error creating draft: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_emails(self, query: str, max_results: int = 10) -> dict:
        """
        Search Gmail for messages.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            dict with list of messages
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full details for each message
            email_list = []
            for msg in messages:
                full_msg = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] 
                          for h in full_msg['payload']['headers']}
                
                email_list.append({
                    'id': msg['id'],
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', '')
                })
            
            return {
                "status": "success",
                "count": len(email_list),
                "messages": email_list
            }
            
        except Exception as e:
            self.logger.error(f"Error searching emails: {e}")
            return {"status": "error", "message": str(e)}
    
    def mark_read(self, message_ids: list) -> dict:
        """
        Mark emails as read.
        
        Args:
            message_ids: List of message IDs to mark as read
            
        Returns:
            dict with status
        """
        try:
            for msg_id in message_ids:
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            
            self.logger.info(f"Marked {len(message_ids)} messages as read")
            
            return {
                "status": "success",
                "marked_count": len(message_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Error marking as read: {e}")
            return {"status": "error", "message": str(e)}


def create_mcp_server():
    """Create and run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP library not available. Running in standalone mode.")
        return
    
    server = Server("email-mcp")
    email_service = EmailMCPServer()
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="send_email",
                description="Send an email via Gmail",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"},
                        "attachments": {"type": "array", "items": {"type": "string"}, "description": "File paths to attach"},
                        "html": {"type": "boolean", "description": "Whether body is HTML"}
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="create_draft",
                description="Create a draft email (requires approval to send)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"},
                        "attachments": {"type": "array", "items": {"type": "string"}, "description": "File paths to attach"},
                        "html": {"type": "boolean", "description": "Whether body is HTML"}
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="search_emails",
                description="Search Gmail for messages",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query"},
                        "max_results": {"type": "integer", "description": "Max results"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="mark_read",
                description="Mark emails as read",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_ids": {"type": "array", "items": {"type": "string"}, "description": "Message IDs to mark as read"}
                    },
                    "required": ["message_ids"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "send_email":
            result = email_service.send_email(
                to=arguments.get("to"),
                subject=arguments.get("subject"),
                body=arguments.get("body"),
                attachments=arguments.get("attachments"),
                html=arguments.get("html", False)
            )
        elif name == "create_draft":
            result = email_service.create_draft(
                to=arguments.get("to"),
                subject=arguments.get("subject"),
                body=arguments.get("body"),
                attachments=arguments.get("attachments"),
                html=arguments.get("html", False)
            )
        elif name == "search_emails":
            result = email_service.search_emails(
                query=arguments.get("query"),
                max_results=arguments.get("max_results", 10)
            )
        elif name == "mark_read":
            result = email_service.mark_read(
                message_ids=arguments.get("message_ids", [])
            )
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return server


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--port', type=int, default=8809, help='Server port')
    parser.add_argument('--credentials', help='Path to credentials.json')
    parser.add_argument('--token', help='Path to token.json')
    
    args = parser.parse_args()
    
    if not MCP_AVAILABLE:
        print("MCP not available. Run in standalone mode for testing.")
        # Test in standalone mode
        email_service = EmailMCPServer(args.credentials, args.token)
        print(f"Dry run mode: {email_service.dry_run}")
        print("Email MCP Server ready (standalone mode)")
        return
    
    server = create_mcp_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
