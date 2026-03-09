# AI Employee - Gold Tier

A local-first autonomous AI agent that manages your personal and business affairs using **Qwen Code** and **Obsidian**.

## Quick Start

### 1. Setup Environment Variables

```bash
# Copy example file
copy .env.example .env

# Edit .env and fill in your values
# See ENV_SETUP_GUIDE.md for detailed instructions
```

### 2. Install Dependencies

```bash
cd scripts
pip install -r requirements-gold.txt
playwright install chromium
```

### 3. Start Odoo (Docker Required)

```bash
cd odoo
docker-compose up -d
```

### 4. Authenticate Services

```bash
python scripts/gmail_authenticate.py
python scripts/linkedin_watcher.py --setup
python scripts/facebook_watcher.py --setup
```

## Usage

### Ralph Wiggum Loop (Autonomous Tasks)

```bash
# Process until complete
python scripts/ralph_wiggum.py "Process all files in Needs_Action"

# With completion promise
python scripts/ralph_wiggum.py "Generate weekly report" \
  --completion-promise "TASK_COMPLETE"
```

### Odoo Accounting

```bash
# Get account summary
python scripts/odoo_mcp_server.py

# Via Qwen Code
qwen "Get weekly revenue from Odoo"
```

### Audit Logs

```bash
# View today's audit log
type AI_Employee_Vault\Logs\audit\2026-03-06.json
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
├── Inbox/                 # Drop files here
├── Needs_Action/          # Pending tasks
├── Plans/                 # Task plans
├── Done/                  # Completed tasks
├── Pending_Approval/      # Awaiting approval
├── Approved/              # Approved actions
├── Rejected/              # Rejected actions
├── Logs/
│   ├── audit/            # Audit logs (JSON)
│   └── *.log             # System logs
├── Accounting/            # Financial records
├── Briefings/             # CEO briefings
└── Invoices/              # Invoice files
```

## Gold Tier Features

### Odoo ERP Integration

Self-hosted accounting via Docker:
- Create invoices
- Manage customers
- Track revenue
- Generate reports

```bash
cd odoo
docker-compose up -d
```

### Facebook Integration

Monitor and post to Facebook:
- Notifications watcher
- Post updates
- Page management

### Ralph Wiggum Loop

Autonomous multi-step task completion:
- Self-correcting execution
- Continues until complete
- Configurable max iterations

### Audit Logging

Comprehensive audit trail:
- All actions logged
- Query by date/type/actor
- Daily summaries
- Export capability

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
                    ┌────────────▼────────────┐
                    │    Needs_Action         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Orchestrator         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Qwen Code            │
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

## Troubleshooting

### Odoo Not Starting

```bash
docker-compose logs odoo
docker-compose restart
```

### Session Expired

```bash
python scripts/linkedin_watcher.py --setup
python scripts/facebook_watcher.py --setup
```

### Ralph Loop Not Completing

1. Increase max iterations
2. Simplify the task
3. Review Qwen output for errors

## Security Notes

- Never commit credentials or tokens
- Store session data outside vault
- Use dry-run mode for testing
- Review audit logs regularly
- Social media automation may violate ToS
- Odoo should be behind firewall

## Documentation

- [Gold Tier Guide](./GOLD_TIER.md) - Detailed documentation
- [Silver Tier Guide](./SILVER_TIER.md) - Silver Tier features
- [Hackathon Blueprint](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)

## Resources

- [Qwen Code Docs](https://github.com/anthropics/qwen-code)
- [Obsidian Help](https://help.obsidian.md/)
- [Odoo Documentation](https://www.odoo.com/documentation)
- [Docker Compose](https://docs.docker.com/compose/)
- [Playwright Docs](https://playwright.dev/)
