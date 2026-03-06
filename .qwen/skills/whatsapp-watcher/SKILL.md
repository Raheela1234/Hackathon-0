---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages containing priority keywords.
  Uses Playwright to automate WhatsApp Web and detect unread messages.
  Creates action files in /Needs_Action for Qwen Code to process.
  Supports keyword filtering, session persistence, and automatic deduplication.
---

# WhatsApp Watcher Skill

Monitor WhatsApp Web for important messages using browser automation.

## Prerequisites

1. **Playwright installed:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **WhatsApp Web account:** Must be logged in on first run

## Setup

### 1. Install Dependencies

```bash
cd scripts
pip install -r requirements-whatsapp.txt
```

### 2. First Run (Session Creation)

```bash
python scripts/whatsapp_watcher.py /path/to/vault --setup
```

This opens a browser where you can scan the QR code to log in.
Session data is saved for future runs.

## Usage

### Start WhatsApp Watcher

```bash
# Default vault path
python scripts/whatsapp_watcher.py

# Custom vault path
python scripts/whatsapp_watcher.py /path/to/vault

# Custom check interval (seconds)
python scripts/whatsapp_watcher.py /path/to/vault --interval 30

# Custom session path
python scripts/whatsapp_watcher.py --session /path/to/session
```

### Configuration

Create `.env` file:

```bash
# .env (add to .gitignore!)
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session
VAULT_PATH=/path/to/AI_Employee_Vault
CHECK_INTERVAL=30
```

## Features

### Keyword Filtering

Automatically detects messages containing:
- `urgent`, `asap`, `emergency`
- `invoice`, `payment`, `billing`
- `help`, `support`, `question`

### Session Persistence

- Browser session saved between runs
- No need to scan QR code every time
- Session stored securely outside vault

### Priority Detection

- **High**: Contains priority keywords
- **Medium**: From known contacts
- **Low**: General messages

## Output Format

Creates files in `/Needs_Action/`:

```markdown
---
type: whatsapp
from: +1234567890
received: 2026-03-05T10:30:00
priority: high
status: pending
---

## WhatsApp Message

**From:** +1234567890
**Received:** 2026-03-05 10:30:00

## Message Content

[Message text here]

## Suggested Actions

- [ ] Reply via WhatsApp
- [ ] Take appropriate action
- [ ] Mark as complete

## Notes

<!-- Add notes here -->
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code every time | Check session path is writable |
| No messages detected | Ensure WhatsApp Web is loaded |
| Browser crashes | Increase check interval |
| Playwright error | Run `playwright install chromium` |

## Security Notes

- Session data contains authentication tokens
- Never commit session files to git
- Store session outside vault
- Log out of WhatsApp Web when not in use

## Terms of Service

**Important:** Using automated tools with WhatsApp may violate WhatsApp's Terms of Service. Use at your own risk and consider:

1. Using WhatsApp Business API for production
2. Respecting rate limits
3. Not using for spam or unsolicited messages
