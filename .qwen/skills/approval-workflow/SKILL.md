---
name: approval-workflow
description: |
  Human-in-the-Loop (HITL) approval workflow for sensitive actions.
  Manages approval requests in /Pending_Approval, /Approved, and /Rejected folders.
  Supports automatic execution of approved actions via MCP servers.
---

# Approval Workflow Skill

Human-in-the-Loop approval system for sensitive actions.

## Overview

When Qwen Code detects a sensitive action (payments, email sends, etc.), it:

1. Creates an approval request file in `/Pending_Approval/`
2. Waits for human review
3. Human moves file to `/Approved/` or `/Rejected/`
4. Orchestrator executes approved actions

## Folder Structure

```
AI_Employee_Vault/
├── Pending_Approval/    # Awaiting human review
├── Approved/            # Approved and ready to execute
├── Rejected/            # Rejected actions
└── Logs/
    └── approvals/       # Approval audit logs
```

## Approval Request Format

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #123
amount: 500.00
created: 2026-03-05T10:30:00Z
expires: 2026-03-06T10:30:00Z
status: pending
---

# Approval Request

## Action Details
- **Type:** Send Email
- **To:** client@example.com
- **Subject:** Invoice #123

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.

## Notes
<!-- Add any additional context here -->
```

## Usage

### Create Approval Request

Qwen Code creates approval requests automatically when detecting sensitive actions:

```python
# In Qwen Code prompt
# When action requires approval:
approval = create_approval_request(
    action="send_email",
    params={"to": "client@example.com", "subject": "Invoice"},
    reason="Client invoice requires approval before sending"
)
```

### Review and Approve

1. Check `/Pending_Approval/` folder regularly
2. Review the action details
3. Move file to `/Approved/` to approve
4. Move file to `/Rejected/` to reject

### Execute Approved Actions

```bash
# Orchestrator automatically processes approved files
python scripts/orchestrator.py

# Or manually process
python scripts/approval_executor.py
```

## Auto-Approval Rules

Configure auto-approval for low-risk actions in `Company_Handbook.md`:

```markdown
## Auto-Approval Thresholds

| Action Type | Auto-Approve If |
|-------------|-----------------|
| Email send | To known contacts, < 5 recipients |
| Payment | Amount < $50, existing payee |
| Social post | Scheduled posts only |
```

## Audit Logging

All approvals are logged in `/Logs/approvals/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-03-05T10:30:00Z",
  "action_type": "send_email",
  "actor": "qwen_code",
  "target": "client@example.com",
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

## Expiration

Approval requests expire after 24 hours by default. Expired requests:

1. Are moved to `/Rejected/`
2. Log expiration reason
3. Notify human via dashboard update

## Security Notes

- Never auto-approve payments to new recipients
- Always require approval for amounts > $100
- Review approval logs weekly
- Rotate approval credentials monthly
