---
name: email-mcp-server
description: |
  MCP (Model Context Protocol) server for sending emails via Gmail.
  Provides tools for Qwen Code to send, draft, and search emails.
  Supports human-in-the-loop approval workflow for sensitive actions.
---

# Email MCP Server Skill

MCP server for email operations with Gmail integration.

## Setup

### 1. Install Dependencies

```bash
cd scripts
pip install -r requirements-email-mcp.txt
```

### 2. Configure Credentials

Ensure Gmail credentials are set up (same as Gmail Watcher):

```bash
python scripts/gmail_authenticate.py
```

### 3. Start MCP Server

```bash
# Start the email MCP server
python scripts/email_mcp_server.py

# Or with custom port
python scripts/email_mcp_server.py --port 8809
```

## Usage with Qwen Code

### Configure in Qwen Code MCP settings

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": ["/path/to/scripts/email_mcp_server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "/path/to/token.json"
      }
    }
  }
}
```

### Available Tools

#### send_email

Send an email immediately.

```python
# Tool call
email_send_email(
    to="recipient@example.com",
    subject="Invoice #123",
    body="Please find attached your invoice...",
    attachments=["/path/to/invoice.pdf"]
)
```

#### draft_email

Create a draft email (requires approval to send).

```python
# Tool call
email_draft_email(
    to="recipient@example.com",
    subject="Proposal",
    body="Here is the proposal we discussed..."
)
```

#### search_emails

Search Gmail for messages.

```python
# Tool call
email_search_emails(
    query="is:unread from:client@example.com",
    max_results=10
)
```

#### mark_read

Mark emails as read.

```python
# Tool call
email_mark_read(message_ids=["msg_id_1", "msg_id_2"])
```

## Human-in-the-Loop Pattern

For sensitive actions, use the approval workflow:

1. **Qwen Code creates approval request:**
   ```markdown
   # /Pending_Approval/EMAIL_send_client.md
   ---
   action: send_email
   to: client@example.com
   subject: Invoice #123
   status: pending
   ---
   ```

2. **Human reviews and moves to /Approved/**

3. **Orchestrator executes the action via MCP**

## Dry Run Mode

For testing, enable dry run mode:

```bash
export DRY_RUN=true
python scripts/email_mcp_server.py
```

All emails will be logged but not sent.

## Security Notes

- Never commit credentials or tokens
- Use environment variables for paths
- Enable 2FA on Gmail account
- Use app-specific password if needed
- Review audit logs regularly

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run gmail_authenticate.py |
| Email not sending | Check Gmail API quota |
| MCP connection failed | Verify server is running on correct port |
