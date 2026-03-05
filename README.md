# AI Employee - Bronze Tier

A local-first autonomous AI agent that manages your personal and business affairs using **Qwen Code** and **Obsidian**.

## Overview

This Bronze Tier implementation provides the foundation for your Personal AI Employee:

- **Obsidian Vault** with Dashboard and Company Handbook
- **File System Watcher** that monitors for new files to process
- **Orchestrator** that triggers Qwen Code to process pending tasks
- **Human-in-the-Loop** architecture for safe automation

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Qwen Code](https://github.com/anthropics/qwen-code) | Latest | AI reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers (future) |

## Quick Start

### 1. Install Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

### 2. Open the Vault in Obsidian

Open the `AI_Employee_Vault` folder in Obsidian to access:
- `Dashboard.md` - Real-time status overview
- `Company_Handbook.md` - Rules and guidelines for your AI

### 3. Start the File System Watcher

```bash
# From the project root directory
python scripts/filesystem_watcher.py
```

This watches the `AI_Employee_Vault/Inbox` folder for new files.

### 4. Start the Orchestrator (in a new terminal)

```bash
# From the project root directory
python scripts/orchestrator.py
```

This processes items in `Needs_Action` using Claude Code.

## Usage

### Processing Files

1. **Drop a file** in `AI_Employee_Vault/Inbox/`
2. The **File System Watcher** detects it and creates an action file
3. The **Orchestrator** triggers Claude Code to process it
4. Claude reads the `Company_Handbook.md` for rules
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
├── Plans/                 # Task plans created by Claude
├── Done/                  # Completed tasks
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Approved actions (ready to execute)
├── Rejected/              # Rejected actions
├── Logs/                  # System logs
├── Accounting/            # Financial records
├── Briefings/             # CEO briefings (future)
└── Invoices/              # Invoice files (future)
```

## Configuration

### Watcher Settings

Edit `scripts/filesystem_watcher.py` to customize:

```python
# Check interval (default: 30 seconds)
watcher = FileSystemWatcher(vault_path, check_interval=30)
```

### Orchestrator Settings

Edit `scripts/orchestrator.py` to customize:

```python
# Check interval (default: 60 seconds)
orchestrator = Orchestrator(vault_path, check_interval=60)
```

## Company Handbook

The `Company_Handbook.md` defines how your AI Employee should behave:

- **Communication Guidelines** - How to handle emails and messages
- **Financial Rules** - Payment approval thresholds
- **Task Priorities** - Critical vs. low priority handling
- **Error Handling** - What to do when things go wrong

Customize this file to match your preferences!

## Troubleshooting

### Qwen Code Not Found

```bash
# Install Qwen Code globally
npm install -g @anthropics/qwen-code

# Verify installation
qwen --version
```

### Watcher Not Detecting Files

1. Check the watcher is running: `ps aux | grep filesystem_watcher`
2. Check logs in `AI_Employee_Vault/Logs/`
3. Ensure file permissions allow reading the Inbox folder

### Orchestrator Not Processing

1. Verify Qwen Code is installed and working
2. Check logs in `AI_Employee_Vault/Logs/orchestrator_*.log`
3. Run with `--status` flag to see pending items

## Next Steps (Silver Tier)

To upgrade to Silver Tier, add:

1. **Gmail Watcher** - Monitor email for important messages
2. **MCP Server** - Enable sending emails automatically
3. **Approval Workflow** - Human-in-the-loop for sensitive actions
4. **Scheduled Tasks** - cron/Task Scheduler integration

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   File Drop     │────▶│  File Watcher   │────▶│  Needs_Action   │
│   (Inbox)       │     │  (Python)       │     │   (Folder)      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Done          │◀────│  Qwen Code      │◀────│  Orchestrator   │
│   (Folder)      │     │  (Reasoning)    │     │  (Python)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Security Notes

- All data stays local in your Obsidian vault
- No credentials are stored in the vault
- Sensitive actions require manual approval
- Review logs regularly for audit trail

## License

This project is part of the Personal AI Employee Hackathon 0.

## Resources

- [Hackathon Blueprint](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Claude Code Docs](https://claude.com/product/claude-code)
- [Obsidian Help](https://help.obsidian.md/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
