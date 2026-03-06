# AI Employee - Silver Tier

A local-first autonomous AI agent that manages your personal and business affairs using **Qwen Code** and **Obsidian**.

## Overview

This Silver Tier implementation provides a fully functional AI Employee:

- **Obsidian Vault** with Dashboard and Company Handbook
- **File System Watcher** - Monitor Inbox folder for files
- **Gmail Watcher** - Monitor Gmail for important emails
- **LinkedIn Watcher** - Monitor LinkedIn for notifications and connection requests
- **Email MCP Server** - Send emails via Gmail
- **LinkedIn MCP Server** - Post updates, manage connections
- **Approval Workflow** - Human-in-the-loop for sensitive actions
- **Scheduler** - Automated daily/weekly tasks
- **Orchestrator** - Coordinates all watchers and Qwen Code

## Tiers

### Bronze Tier (Complete)
- File System Watcher
- Basic folder structure
- Dashboard and Company Handbook
- Qwen Code integration

### Silver Tier (Complete)
- All Bronze features plus:
- Gmail Watcher (uses your credentials.json)
- LinkedIn Watcher (Playwright-based)
- Email MCP Server
- LinkedIn MCP Server
- Approval Workflow
- Task Scheduler

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Qwen Code](https://github.com/anthropics/qwen-code) | Latest | AI reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers |
| [Playwright](https://playwright.dev/) | Latest | Browser automation |

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

Your `credentials.json` is already in the project root. Run:

```bash
python scripts/gmail_authenticate.py
```

This will open a browser. Sign in with your Google account.

### 3. Setup LinkedIn Session

```bash
python scripts/linkedin_watcher.py --setup
```

Log in to LinkedIn and close the browser when done.

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

## Usage

### Processing Files

1. **Drop a file** in `AI_Employee_Vault/Inbox/`
2. The **File System Watcher** detects it and creates an action file
3. The **Orchestrator** triggers Qwen Code to process it
4. Qwen reads the `Company_Handbook.md` for rules
5. Completed tasks move to `AI_Employee_Vault/Done/`

### Manual Processing

You can also manually trigger Qwen Code:

```bash
cd AI_Employee_Vault
qwen "Process all files in Needs_Action folder"
```

### Check Status

```bash
python scripts/orchestrator.py --status
```

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md           # Real-time status overview
├── Company_Handbook.md    # Rules and guidelines
├── Inbox/                 # Drop files here for processing
├── Needs_Action/          # Pending tasks (auto-populated)
├── Plans/                 # Task plans created by Qwen
├── Done/                  # Completed tasks
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Approved actions (ready to execute)
├── Rejected/              # Rejected actions
├── Logs/                  # System logs
├── Accounting/            # Financial records
├── Briefings/             # CEO briefings
└── Invoices/              # Invoice files
```

## Watchers

### Gmail Watcher

Monitors Gmail for important/unread emails.

```bash
# Start watcher
python scripts/gmail_watcher.py

# Custom interval (seconds)
python scripts/gmail_watcher.py --interval 60
```

**Priority Keywords:** urgent, asap, invoice, payment, help, client

### LinkedIn Watcher

Monitors LinkedIn for notifications and connection requests.

```bash
# First time setup
python scripts/linkedin_watcher.py --setup

# Start watcher
python scripts/linkedin_watcher.py

# Custom interval (default: 300 seconds)
python scripts/linkedin_watcher.py --interval 600
```

### File System Watcher

Monitors Inbox folder for new files.

```bash
python scripts/filesystem_watcher.py
```

## MCP Servers

### Email MCP Server

Send emails via Gmail with approval workflow.

```bash
python scripts/email_mcp_server.py
```

### LinkedIn MCP Server

Post updates and manage connections.

```bash
python scripts/linkedin_mcp_server.py
```

## Approval Workflow

Sensitive actions require human approval:

1. Qwen Code creates file in `/Pending_Approval/`
2. Human reviews and moves to `/Approved/` or `/Rejected/`
3. Orchestrator executes approved actions

```bash
# Start approval monitor
python scripts/approval_workflow.py
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

## Configuration

### Gmail Credentials

Your `credentials.json` should be in the project root:

```json
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
    "auth_uri": "...",
    "token_uri": "...",
    "client_secret": "..."
  }
}
```

### Environment Variables

```bash
# Dry run mode (test without sending)
export DRY_RUN=true

# Custom paths
export GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
export LINKEDIN_SESSION_PATH=/path/to/session
```

## Troubleshooting

### Qwen Code Not Found

```bash
npm install -g @anthropics/qwen-code
qwen --version
```

### Gmail Authentication Failed

```bash
# Delete old token and re-authenticate
rm ~/.gmail/token.json
python scripts/gmail_authenticate.py
```

### LinkedIn Not Detecting Activity

1. Re-run setup: `python scripts/linkedin_watcher.py --setup`
2. Check LinkedIn is accessible manually
3. Increase check interval

### Playwright Browser Issues

```bash
playwright install chromium --force
```

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

## Security Notes

- Never commit `credentials.json` or `token.json`
- Store session data outside vault
- Use dry-run mode for testing
- Review approval logs regularly
- LinkedIn automation may violate ToS - use at your own risk

## Documentation

- [Silver Tier Guide](./SILVER_TIER.md) - Detailed Silver Tier documentation
- [Hackathon Blueprint](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)

## Skills

Detailed skill documentation in `.qwen/skills/`:

- `gmail-watcher/` - Gmail monitoring
- `linkedin-watcher/` - LinkedIn monitoring
- `email-mcp-server/` - Email sending via MCP
- `approval-workflow/` - Human-in-the-loop approvals
- `scheduling/` - Automated task scheduling
- `browsing-with-playwright/` - Browser automation

## Next Steps (Gold Tier)

To upgrade to Gold Tier:

1. **Odoo Integration** - Accounting via Odoo Community
2. **Social Media Expansion** - Facebook, Instagram, Twitter
3. **Ralph Wiggum Loop** - Autonomous multi-step completion
4. **Comprehensive Audit Logging** - Full action audit trail

## Resources

- [Qwen Code Docs](https://github.com/anthropics/qwen-code)
- [Obsidian Help](https://help.obsidian.md/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Playwright Docs](https://playwright.dev/)
- [Gmail API](https://developers.google.com/gmail/api)
