# Personal AI Employee Hackathon 0

## Project Overview

This repository contains the architectural blueprint and resources for **Hackathon 0: Building Autonomous FTEs (Full-Time Equivalent) in 2026**. The project proposes a local-first AI agent system that proactively manages personal and business affairs 24/7 using:

- **Claude Code** as the reasoning engine
- **Obsidian** as the knowledge base and GUI dashboard
- **Python Watcher scripts** for monitoring external inputs (Gmail, WhatsApp, filesystems)
- **MCP (Model Context Protocol) servers** for external actions (email, payments, social media)

The architecture transforms AI from a reactive chatbot into a proactive "Digital Employee" that works autonomously with human-in-the-loop safeguards.

## Directory Structure

```
Hackathon-0/
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main hackathon blueprint
├── QWEN.md                     # This file - project context
├── skills-lock.json            # Skill dependencies lock file
├── .gitattributes              # Git text normalization config
└── .qwen/skills/               # Installed Qwen skills
    └── browsing-with-playwright/
```

## Key Concepts

### Digital FTE vs Human FTE

| Feature | Human FTE | Digital FTE |
|---------|-----------|-------------|
| Availability | 40 hours/week | 168 hours/week (24/7) |
| Monthly Cost | $4,000–$8,000+ | $500–$2,000 |
| Annual Hours | ~2,000 | ~8,760 |
| Cost per Task | ~$5.00 | ~$0.50 |

### Architecture Layers

1. **Perception (Watchers)**: Python scripts monitoring Gmail, WhatsApp, filesystems
2. **Memory/GUI (Obsidian)**: Local Markdown vault with Dashboard.md, Company_Handbook.md
3. **Reasoning (Claude Code)**: AI engine that reads, thinks, plans, and writes
4. **Action (MCP Servers)**: External integrations for email, browser automation, payments
5. **Orchestration**: Master process handling scheduling and folder watching

### Human-in-the-Loop (HITL)

Sensitive actions require approval via file movement:
- Claude creates approval requests in `/Pending_Approval/`
- Human reviews and moves to `/Approved/` or `/Rejected/`
- Orchestrator executes approved actions via MCP

## Hackathon Tiers

| Tier | Requirements | Time Estimate |
|------|--------------|---------------|
| **Bronze** | Obsidian vault, 1 Watcher, basic folder structure | 8-12 hours |
| **Silver** | 2+ Watchers, MCP server, approval workflow, scheduling | 20-30 hours |
| **Gold** | Full integration, Odoo accounting, Ralph Wiggum loop, audit logging | 40+ hours |
| **Platinum** | Cloud deployment, domain specialization, 24/7 operation | 60+ hours |

## Prerequisites

### Required Software
- Claude Code (active subscription)
- Obsidian v1.10.6+
- Python 3.13+
- Node.js v24+ LTS
- GitHub Desktop

### Hardware
- Minimum: 8GB RAM, 4-core CPU, 20GB free disk
- Recommended: 16GB RAM, 8-core CPU, SSD

## Installed Skills

- **browsing-with-playwright**: Browser automation via Playwright for web-based interactions

## Usage

1. Read the main blueprint document for full architecture details
2. Set up Obsidian vault with required folder structure (`/Inbox`, `/Needs_Action`, `/Done`)
3. Implement Watcher scripts following the base pattern in the blueprint
4. Configure MCP servers for external integrations
5. Use Claude Code as the reasoning engine pointed at your vault

## Key Resources

- [Claude Code Fundamentals](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [MCP Introduction](https://modelcontextprotocol.io/introduction)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Odoo 19 External API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)

## Security Notes

- Never commit `.env` files or credentials
- Use environment variables for API keys
- Implement dry-run mode for development
- Maintain audit logs for all actions
- Require human approval for sensitive operations (payments, new contacts)

## Weekly Meetings

Research and Showcase meetings every Wednesday at 10:00 PM PKT on Zoom:
- Meeting ID: 871 8870 7642
- Passcode: 744832
- First meeting: January 7th, 2026
