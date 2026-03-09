# Gold Tier - Complete Implementation

## Overview

Gold Tier transforms your AI Employee into a fully autonomous business assistant with accounting integration, social media management, and self-correcting task completion.

**Estimated Time:** 40+ hours

## What's Included

### New Watchers (Perception Layer)

| Watcher | Purpose | Check Interval |
|---------|---------|----------------|
| File System | Monitor Inbox folder for files | 30 seconds |
| Gmail | Monitor Gmail for important emails | 120 seconds |
| LinkedIn | Monitor LinkedIn for notifications | 300 seconds |
| Facebook | Monitor Facebook for activity | 300 seconds |

### New MCP Servers (Action Layer)

| Server | Capabilities |
|--------|-------------|
| Email MCP | Send emails, create drafts, search Gmail |
| LinkedIn MCP | Post updates, accept connections, send messages |
| Facebook MCP | Post updates, post to pages |
| Odoo MCP | Create invoices, manage customers, accounting reports |

### Gold Tier Features

- **Odoo ERP Integration** - Self-hosted accounting via Docker
- **Facebook Integration** - Monitor and post to Facebook
- **Ralph Wiggum Loop** - Autonomous multi-step task completion
- **Comprehensive Audit Logging** - Full action audit trail
- **Error Recovery** - Graceful degradation on failures
- **Weekly CEO Briefing** - Automated business reports

## Quick Start

### 1. Install Dependencies

```bash
cd scripts

# Install all Gold Tier dependencies
pip install -r requirements-gold.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Start Odoo (Docker Required)

```bash
# Install Docker Desktop if not installed
# https://www.docker.com/products/docker-desktop

cd odoo
docker-compose up -d

# Wait for Odoo to start (2-3 minutes)
# Access at: http://localhost:8069
# Default login: admin / admin
```

### 3. Authenticate Services

```bash
# Gmail (uses your credentials.json)
python scripts/gmail_authenticate.py

# LinkedIn (first time setup)
python scripts/linkedin_watcher.py --setup

# Facebook (first time setup)
python scripts/facebook_watcher.py --setup
```

### 4. Start All Watchers

Open multiple terminals:

```bash
# Terminal 1: File System Watcher
python scripts/filesystem_watcher.py

# Terminal 2: Gmail Watcher
python scripts/gmail_watcher.py

# Terminal 3: LinkedIn Watcher
python scripts/linkedin_watcher.py

# Terminal 4: Facebook Watcher
python scripts/facebook_watcher.py

# Terminal 5: Orchestrator
python scripts/orchestrator.py

# Terminal 6: Approval Workflow
python scripts/approval_workflow.py
```

### 5. Start MCP Servers (Optional)

```bash
# Email MCP Server
python scripts/email_mcp_server.py

# LinkedIn MCP Server
python scripts/linkedin_mcp_server.py

# Facebook MCP Server
python scripts/facebook_mcp_server.py

# Odoo MCP Server
python scripts/odoo_mcp_server.py
```

## Odoo Integration

### Docker Compose Setup

The Odoo setup includes:
- Odoo 19.0 Community Edition
- PostgreSQL database
- Persistent data storage
- Health monitoring

```yaml
# odoo/docker-compose.yml
services:
  odoo:
    image: odoo:19.0
    ports:
      - "8069:8069"
  db:
    image: postgres:15
```

### Access Odoo

1. Open http://localhost:8069
2. Master password: `admin`
3. Create your first database
4. Install Accounting app

### Odoo MCP Server Tools

#### Get Invoices
```python
odoo_get_invoices(limit=10, state="posted")
```

#### Create Invoice
```python
odoo_create_invoice(
    partner_id=1,
    amount=500.00,
    description="Consulting Services"
)
```

#### Get Account Summary
```python
odoo_get_account_summary()
```

#### Get Weekly Revenue
```python
odoo_get_weekly_revenue()
```

### Environment Variables

```bash
export ODOO_URL=http://localhost:8069
export ODOO_DB=odoo
export ODOO_USERNAME=admin
export ODOO_PASSWORD=admin
```

## Facebook Integration

### Facebook Watcher

Monitors Facebook for:
- New notifications
- Unread messages
- Page activity
- Comments and reactions

```bash
# First time setup (login)
python scripts/facebook_watcher.py --setup

# Start watcher
python scripts/facebook_watcher.py

# Custom interval
python scripts/facebook_watcher.py --interval 600
```

### Facebook MCP Server

Post updates to your profile or pages:

```python
# Post to personal profile
facebook_post_update(
    content="Exciting news about our product launch!",
    privacy="public"
)

# Post to page
facebook_post_to_page(
    page_name="My Business Page",
    content="Check out our latest offers!"
)
```

### Output Format

Creates files in `Needs_Action/`:
```
FACEBOOK_message_20260306_170000.md
FACEBOOK_comment_20260306_171500.md
FACEBOOK_reaction_20260306_173000.md
```

## Ralph Wiggum Loop

Autonomous multi-step task completion:

```bash
# Process all pending items until complete
python scripts/ralph_wiggum.py "Process all files in Needs_Action"

# With completion promise
python scripts/ralph_wiggum.py "Generate weekly report" \
  --completion-promise "TASK_COMPLETE"

# Custom max iterations
python scripts/ralph_wiggum.py "Audit accounting" --max-iterations 20
```

### How It Works

1. Start Qwen Code with prompt
2. Monitor for exit attempt
3. Check if task is complete
4. If not complete, re-inject prompt and continue
5. Repeat until complete or max iterations

### Use Cases

- Multi-step data processing
- Complex report generation
- Batch invoice creation
- Cross-system synchronization

## Audit Logging

Comprehensive audit trail for all actions:

```python
from audit_logger import AuditLogger

logger = AuditLogger(vault_path)

# Log an action
logger.log_action(
    action_type='invoice_create',
    actor='qwen_code',
    target='Customer ABC',
    parameters={'amount': 500},
    approval_status='approved',
    approved_by='human',
    result='success'
)

# Query logs
logs = logger.get_actions(
    date='2026-03-06',
    action_type='invoice_create'
)

# Get daily summary
summary = logger.get_daily_summary()
```

### Log Location

```
AI_Employee_Vault/
└── Logs/
    └── audit/
        ├── 2026-03-06.json
        ├── 2026-03-07.json
        └── ...
```

### Log Retention

```bash
# Cleanup logs older than 90 days
python -c "
from audit_logger import AuditLogger
logger = AuditLogger('/path/to/vault')
logger.cleanup_old_logs(days_to_keep=90)
"
```

## Weekly CEO Briefing

Automated business summary generation:

```bash
# Run weekly audit
python scripts/scheduler.py run weekly_audit
```

### Output Format

```markdown
# Monday Morning CEO Briefing

## Executive Summary
Strong week with revenue ahead of target.

## Revenue
- **This Week**: $2,450
- **MTD**: $4,500 (45% of $10,000 target)
- **Trend**: On track

## Completed Tasks
- [x] Client A invoice sent and paid
- [x] Project Alpha milestone delivered

## Odoo Accounting Summary
- Total Receivable: $12,500
- Total Payable: $3,200
- Net Position: $9,300

## Social Media Activity
- LinkedIn: 5 new connections
- Facebook: 12 new page likes

## Proactive Suggestions
- Notion: No activity in 45 days. Cancel?
```

## Configuration

### Odoo Configuration

Edit `odoo/odoo-config/odoo.conf`:

```ini
[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo_password
```

### Environment Variables

```bash
# Odoo
export ODOO_URL=http://localhost:8069
export ODOO_DB=odoo
export ODOO_USERNAME=admin
export ODOO_PASSWORD=admin

# Dry run mode (test without posting)
export DRY_RUN=true
```

## Troubleshooting

### Odoo Not Starting

```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs odoo

# Restart
docker-compose down
docker-compose up -d
```

### Facebook/LinkedIn Session Expired

```bash
# Re-run setup
python scripts/facebook_watcher.py --setup
python scripts/linkedin_watcher.py --setup
```

### Ralph Loop Not Completing

1. Check if completion criteria is achievable
2. Increase max iterations
3. Review Qwen Code output for errors
4. Simplify the task into smaller steps

### Audit Logs Not Writing

1. Check Logs/audit directory exists
2. Verify write permissions
3. Check disk space

## Security Notes

- Never commit credentials or tokens
- Store session data outside vault
- Use dry-run mode for testing
- Review audit logs regularly
- Social media automation may violate ToS
- Odoo should be behind firewall for production

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
│   Facebook      │────▶│ Facebook Watcher│
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
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐ ┌─────▼──────┐ ┌────────▼────────┐
    │ Approval Workflow │ │ Ralph      │ │ Audit Logger    │
    │ (HITL)            │ │ Wiggum     │ │ (All Actions)   │
    └───────────────────┘ │ Loop       │ └─────────────────┘
                          └────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐ ┌─────▼──────┐ ┌────────▼────────┐
    │ Email MCP         │ │ LinkedIn   │ │ Facebook MCP    │
    │ (Send Email)      │ │ MCP        │ │ (Post Update)   │
    └───────────────────┘ └────────────┘ └─────────────────┘
                                 │
                          ┌──────▼───────┐
                          │ Odoo MCP     │
                          │ (Accounting) │
                          └──────────────┘
```

## Gold Tier Checklist

- [ ] Odoo Docker container running
- [ ] Gmail authentication complete
- [ ] LinkedIn session setup
- [ ] Facebook session setup
- [ ] All watchers running
- [ ] MCP servers configured
- [ ] Audit logging enabled
- [ ] Ralph Wiggum loop tested
- [ ] Weekly briefing scheduled

## Next Steps (Platinum Tier)

To upgrade to Platinum Tier:

1. **Cloud Deployment** - Run on Oracle/AWS free tier VM
2. **Work-Zone Specialization** - Split Cloud/Local responsibilities
3. **Vault Sync** - Git or Syncthing for multi-agent coordination
4. **A2A Communication** - Direct agent-to-agent messaging
5. **24/7 Operation** - Health monitoring and auto-recovery

## Skills Documentation

Detailed skill documentation in `.qwen/skills/`:

- `gmail-watcher/` - Gmail monitoring
- `linkedin-watcher/` - LinkedIn monitoring
- `facebook-watcher/` - Facebook monitoring
- `odoo-mcp-server/` - Odoo ERP integration
- `email-mcp-server/` - Email sending via MCP
- `approval-workflow/` - Human-in-the-loop approvals
- `scheduling/` - Automated task scheduling
- `ralph-wiggum/` - Autonomous task completion
- `audit-logging/` - Comprehensive audit trail

## Resources

- [Odoo Documentation](https://www.odoo.com/documentation)
- [Odoo 19 External API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Docker Compose](https://docs.docker.com/compose/)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [LinkedIn API](https://learn.microsoft.com/en-us/linkedin/)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
