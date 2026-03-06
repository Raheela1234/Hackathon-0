# Silver Tier - Complete Implementation

## Overview

Silver Tier adds two more watchers (Gmail and LinkedIn) plus MCP servers for external actions.

**Estimated Time:** 20-30 hours

## What's Included

### Watchers (Perception Layer)

| Watcher | Purpose | Check Interval |
|---------|---------|----------------|
| File System | Monitor Inbox folder for files | 30 seconds |
| Gmail | Monitor Gmail for important emails | 120 seconds |
| LinkedIn | Monitor LinkedIn for notifications | 300 seconds |

### MCP Servers (Action Layer)

| Server | Capabilities |
|--------|-------------|
| Email MCP | Send emails, create drafts, search Gmail |
| LinkedIn MCP | Post updates, accept connections, send messages |

### Additional Features

- **Approval Workflow** - Human-in-the-loop for sensitive actions
- **Scheduler** - Automated daily/weekly tasks
- **Orchestrator** - Coordinates all watchers and Qwen Code

## Quick Start

### 1. Install Dependencies

```bash
cd scripts

# Install all Silver Tier dependencies
pip install -r requirements-silver.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Authenticate Gmail

Your `credentials.json` is already in the project root. Run authentication:

```bash
python scripts/gmail_authenticate.py
```

This will open a browser window. Sign in with your Google account and grant permissions.

### 3. Setup LinkedIn Session

```bash
python scripts/linkedin_watcher.py --setup
```

This opens a browser. Log in to LinkedIn and close the browser when done.

### 4. Start All Watchers

Open multiple terminals:

```bash
# Terminal 1: File System Watcher
python scripts/filesystem_watcher.py

# Terminal 2: Gmail Watcher
python scripts/gmail_watcher.py

# Terminal 3: LinkedIn Watcher
python scripts/linkedin_watcher.py

# Terminal 4: Orchestrator
python scripts/orchestrator.py

# Terminal 5: Approval Workflow
python scripts/approval_workflow.py
```

### 5. Start MCP Servers (Optional)

```bash
# Email MCP Server
python scripts/email_mcp_server.py

# LinkedIn MCP Server
python scripts/linkedin_mcp_server.py
```

## Gmail Watcher

### Features

- Monitors unread emails
- Priority detection based on keywords
- Creates action files in `/Needs_Action/`
- Tracks processed emails to avoid duplicates

### Priority Keywords

- `urgent`, `asap`, `emergency`
- `invoice`, `payment`, `billing`
- `help`, `support`, `issue`
- `client`, `customer`, `order`

### Configuration

```bash
# Custom check interval (default: 120 seconds)
python scripts/gmail_watcher.py --interval 60

# Custom token path
python scripts/gmail_watcher.py --token /path/to/token.json
```

### Output Format

Creates files like:
```
Needs_Action/EMAIL_msgId_Subject_Line.md
```

## LinkedIn Watcher

### Features

- Monitors notifications
- Detects connection requests
- Creates action files for Qwen Code

### Activity Types

- Connection requests
- Messages
- Job opportunities
- Congratulation notifications

### Configuration

```bash
# Custom check interval (default: 300 seconds)
python scripts/linkedin_watcher.py --interval 600

# Custom session path
python scripts/linkedin_watcher.py --session /path/to/session
```

### Output Format

Creates files like:
```
Needs_Action/LINKEDIN_connection_request_20260305_143022.md
```

## LinkedIn MCP Server

### Available Tools

#### post_update

Post an update to LinkedIn.

```python
# Via Qwen Code
linkedin_post_update(
    content="Excited to share our new product launch!",
    visibility="public"
)
```

#### accept_connection

Accept a connection request.

```python
linkedin_accept_connection(profile_name="John Doe")
```

#### send_message

Send a message to a connection.

```python
linkedin_send_message(
    recipient_name="Jane Smith",
    message="Hi Jane, thanks for connecting!"
)
```

### Dry Run Mode

Test without posting:

```bash
export DRY_RUN=true
python scripts/linkedin_mcp_server.py
```

## Approval Workflow

Sensitive actions require approval:

1. Qwen Code creates file in `/Pending_Approval/`
2. Human reviews and moves to `/Approved/`
3. Orchestrator executes the action

### Example Approval Request

```markdown
---
type: approval_request
action: linkedin_post_update
content: Excited to announce...
created: 2026-03-05T10:30:00Z
status: pending
---

# Approval Request

## Action: LinkedIn Post

**Content:** Excited to announce our new product...

Move to `/Approved/` to approve.
Move to `/Rejected/` to reject.
```

## Scheduler

Automate regular tasks:

```bash
# Run daily briefing
python scripts/scheduler.py run daily_briefing

# Register scheduled task (Windows)
python scripts/scheduler.py register --task daily_briefing --time "08:00"

# List scheduled tasks
python scripts/scheduler.py list
```

### Pre-built Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| daily_briefing | 8:00 AM daily | Morning business summary |
| weekly_audit | 10:00 PM Sunday | Weekly revenue/bottleneck report |
| process_inbox | Every 2 hours | Process pending items |

## Troubleshooting

### Gmail Authentication Failed

```bash
# Delete old token and re-authenticate
rm ~/.gmail/token.json
python scripts/gmail_authenticate.py
```

### LinkedIn Not Detecting Activity

1. Ensure session is valid: `python scripts/linkedin_watcher.py --setup`
2. Check LinkedIn is accessible manually
3. Increase check interval to avoid rate limiting

### Playwright Browser Issues

```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

### MCP Server Not Connecting

1. Ensure server is running
2. Check port is not in use
3. Verify Qwen Code MCP configuration

## Security Notes

- Never commit `credentials.json` or `token.json`
- Store session data outside vault
- Use dry-run mode for testing
- Review approval logs regularly
- LinkedIn automation may violate ToS - use at your own risk

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│    Gmail        │────▶│  Gmail Watcher  │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│   LinkedIn      │────▶│ LinkedIn Watcher│
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│  File System    │────▶│  File Watcher   │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Needs_Action         │
                    │    (Obsidian Vault)     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Orchestrator         │
                    │    (triggers Qwen)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Qwen Code            │
                    │    (Reasoning)          │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
    ┌─────────▼─────────┐               ┌──────────▼──────────┐
    │ Approval Workflow │               │ MCP Servers         │
    │ (HITL)            │               │ - Email             │
    └───────────────────┘               │ - LinkedIn          │
                                        └─────────────────────┘
```

## Next Steps (Gold Tier)

To upgrade to Gold Tier:

1. **Odoo Integration** - Accounting via Odoo Community
2. **Social Media Expansion** - Facebook, Instagram, Twitter
3. **Ralph Wiggum Loop** - Autonomous multi-step completion
4. **Comprehensive Audit Logging** - Full action audit trail
5. **Error Recovery** - Graceful degradation

## Skills Documentation

Detailed skill documentation:

- `.qwen/skills/gmail-watcher/SKILL.md`
- `.qwen/skills/linkedin-watcher/SKILL.md`
- `.qwen/skills/email-mcp-server/SKILL.md`
- `.qwen/skills/approval-workflow/SKILL.md`
- `.qwen/skills/scheduling/SKILL.md`
