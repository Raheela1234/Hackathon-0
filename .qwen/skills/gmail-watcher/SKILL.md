---
name: gmail-watcher
description: |
  Monitor Gmail for new important/unread emails and create action files in the Obsidian vault.
  Uses Gmail API to fetch emails and creates .md files in /Needs_Action for Qwen Code to process.
  Supports keyword filtering, priority detection, and automatic deduplication.
---

# Gmail Watcher Skill

Monitor Gmail and create actionable files for new important emails.

## Setup

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json`

### 2. Install Dependencies

```bash
cd scripts
pip install -r requirements-gmail.txt
```

### 3. Authenticate

```bash
python scripts/gmail_authenticate.py
```

This creates a `token.json` file with your OAuth credentials.

## Usage

### Start Gmail Watcher

```bash
# Default vault path
python scripts/gmail_watcher.py

# Custom vault path
python scripts/gmail_watcher.py /path/to/vault

# Custom check interval (seconds)
python scripts/gmail_watcher.py /path/to/vault --interval 60
```

### Configuration

Edit environment variables or create `.env` file:

```bash
# .env (add to .gitignore!)
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
VAULT_PATH=/path/to/AI_Employee_Vault
CHECK_INTERVAL=120
```

## Features

### Keyword Filtering

Automatically flags emails containing:
- `urgent`, `asap`, `emergency`
- `invoice`, `payment`, `billing`
- `help`, `support`, `issue`

### Priority Detection

- **High**: From known contacts, contains priority keywords
- **Medium**: Unread important emails
- **Low**: Newsletter, notifications

### Deduplication

Tracks processed email IDs to avoid duplicate action files.

## Output Format

Creates files in `/Needs_Action/`:

```markdown
---
type: email
from: client@example.com
subject: Invoice Request
received: 2026-03-05T10:30:00
priority: high
status: pending
---

## Email Content

[Email snippet here]

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run `gmail_authenticate.py` |
| No emails detected | Check Gmail API quota, verify label filters |
| Duplicate emails | Delete `.cache/gmail_processed.txt` |

## Security Notes

- Never commit `credentials.json` or `token.json`
- Store in secure location outside vault
- Rotate credentials monthly
- Use app-specific passwords if 2FA enabled
