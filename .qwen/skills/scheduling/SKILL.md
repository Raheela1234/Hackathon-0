---
name: scheduling
description: |
  Scheduling utility for running periodic tasks via cron (Linux/Mac) or 
  Task Scheduler (Windows). Supports daily briefings, weekly audits, 
  and custom scheduled Qwen Code prompts.
---

# Scheduling Skill

Automated scheduling for AI Employee tasks.

## Overview

Run periodic tasks automatically:
- **Daily Briefing**: 8:00 AM business summary
- **Weekly Audit**: Sunday night revenue/bottleneck report
- **Custom Tasks**: Any Qwen Code prompt on schedule

## Setup

### Windows (Task Scheduler)

```bash
# Register scheduled task
python scripts/scheduler.py register --task daily_briefing --time "08:00"

# List scheduled tasks
python scripts/scheduler.py list

# Remove task
python scripts/scheduler.py remove --task daily_briefing
```

### Linux/Mac (cron)

```bash
# Install cron jobs
python scripts/scheduler.py install

# View crontab
crontab -l
```

## Pre-built Tasks

### Daily Briefing

Generates morning business summary at 8:00 AM.

```bash
python scripts/scheduler.py run daily_briefing
```

Output: `/Briefings/YYYY-MM-DD_Daily_Briefing.md`

### Weekly Audit

Sunday night revenue and bottleneck analysis.

```bash
python scripts/scheduler.py run weekly_audit
```

Output: `/Briefings/YYYY-MM-DD_Weekly_Audit.md`

### Process Inbox

Process all pending items in `/Needs_Action`.

```bash
python scripts/scheduler.py run process_inbox
```

## Custom Scheduled Tasks

Create custom tasks in `scheduled_tasks.json`:

```json
{
  "tasks": [
    {
      "name": "morning_check",
      "schedule": "0 8 * * *",
      "prompt": "Check /Needs_Action and /Pending_Approval. Update Dashboard.md with status."
    },
    {
      "name": "evening_summary",
      "schedule": "0 18 * * *",
      "prompt": "Summarize today's completed tasks from /Done folder."
    }
  ]
}
```

## Task Output Format

All scheduled tasks create markdown files:

```markdown
---
generated: 2026-03-05T08:00:00Z
task: daily_briefing
period: 2026-03-04 to 2026-03-05
---

# Daily Briefing

## Summary
Brief overview of business status.

## Completed Tasks
- List of tasks from /Done

## Pending Items
- Items still in /Needs_Action

## Upcoming Deadlines
- Deadlines from Business_Goals.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Task not running | Check Task Scheduler/cron logs |
| Qwen not found | Ensure Qwen Code in PATH |
| Permission denied | Run scheduler as admin/root |

## Security Notes

- Scheduled tasks run with user permissions
- Don't schedule sensitive actions without approval
- Review task outputs regularly
- Rotate credentials used in scheduled tasks
