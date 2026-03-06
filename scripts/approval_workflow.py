"""
Approval Workflow Module

Human-in-the-Loop (HITL) approval system for sensitive actions.
Monitors /Pending_Approval, /Approved, and /Rejected folders.
Executes approved actions via MCP servers.

Usage:
    python approval_workflow.py /path/to/vault
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ApprovalWorkflow:
    """
    Manages approval workflow for sensitive actions.
    
    Responsibilities:
    - Create approval request files
    - Monitor /Approved folder for execution
    - Move rejected/expired files
    - Log all approval activities
    """
    
    # Default expiration time (hours)
    DEFAULT_EXPIRATION_HOURS = 24
    
    # Auto-approval thresholds
    AUTO_APPROVE_EMAIL_THRESHOLD = 5  # recipients
    AUTO_APPROVE_PAYMENT_THRESHOLD = 50.00  # dollars
    
    def __init__(self, vault_path: str):
        """
        Initialize approval workflow.
        
        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        
        # Define folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.logs = self.vault_path / 'Logs' / 'approvals'
        self.handbook = self.vault_path / 'Company_Handbook.md'
        
        # Ensure directories exist
        for folder in [self.pending_approval, self.approved, self.rejected, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Load auto-approval rules from handbook
        self.auto_approve_rules = self._load_auto_approve_rules()
    
    def _setup_logging(self):
        """Setup approval logging."""
        import logging
        
        log_file = self.logs / f'approvals_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ApprovalWorkflow')
    
    def _load_auto_approve_rules(self) -> dict:
        """Load auto-approval rules from Company Handbook."""
        rules = {
            'known_contacts': [],
            'existing_payees': [],
            'email_threshold': self.AUTO_APPROVE_EMAIL_THRESHOLD,
            'payment_threshold': self.AUTO_APPROVE_PAYMENT_THRESHOLD
        }
        
        if self.handbook.exists():
            try:
                content = self.handbook.read_text()
                # Parse rules from handbook (simplified parsing)
                # In production, use proper YAML frontmatter parsing
                if 'Auto-Approval' in content:
                    self.logger.info("Loaded auto-approval rules from handbook")
            except Exception as e:
                self.logger.warning(f"Could not parse handbook: {e}")
        
        return rules
    
    def create_approval_request(self, action_type: str, params: dict, 
                                reason: str = None) -> Path:
        """
        Create an approval request file.
        
        Args:
            action_type: Type of action (send_email, payment, etc.)
            params: Action parameters
            reason: Reason for requiring approval
            
        Returns:
            Path to created approval request file
        """
        timestamp = datetime.now()
        expires = timestamp + timedelta(hours=self.DEFAULT_EXPIRATION_HOURS)
        
        # Create safe filename
        safe_action = self._safe_filename(action_type)
        filename = f"APPROVAL_{safe_action}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        
        # Build content
        content = f'''---
type: approval_request
action: {action_type}
created: {timestamp.isoformat()}
expires: {expires.isoformat()}
status: pending
---

# Approval Request

## Action Details

'''
        
        # Add action-specific details
        if action_type == 'send_email':
            content += f'''- **Type:** Send Email
- **To:** {params.get('to', 'Unknown')}
- **Subject:** {params.get('subject', 'Unknown')}
'''
        elif action_type == 'payment':
            content += f'''- **Type:** Payment
- **Amount:** ${params.get('amount', 0):.2f}
- **Recipient:** {params.get('recipient', 'Unknown')}
- **Reference:** {params.get('reference', 'Unknown')}
'''
        else:
            content += f'''- **Type:** {action_type}
'''
        
        # Add all params as JSON for programmatic access
        content += f'''
## Parameters
```json
{json.dumps(params, indent=2)}
```

## Reason for Approval
{reason or 'Action requires human approval per Company Handbook rules.'}

## Instructions

### To Approve
Move this file to `/Approved/` folder.

### To Reject
Move this file to `/Rejected/` folder.

## Notes

<!-- Add any additional context here -->

---
*Created by Approval Workflow*
'''
        
        # Write file
        filepath = self.pending_approval / filename
        filepath.write_text(content, encoding='utf-8')
        
        # Log creation
        self._log_approval('created', action_type, params, 'pending')
        
        self.logger.info(f"Created approval request: {filename}")
        
        return filepath
    
    def process_approved(self) -> list:
        """
        Process all approved actions.
        
        Returns:
            List of execution results
        """
        results = []
        
        for file_path in self.approved.iterdir():
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    result = self._execute_approved_action(file_path)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error executing {file_path.name}: {e}")
                    results.append({
                        'file': file_path.name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results
    
    def _execute_approved_action(self, file_path: Path) -> dict:
        """
        Execute an approved action.
        
        Args:
            file_path: Path to approved action file
            
        Returns:
            Execution result dict
        """
        content = file_path.read_text(encoding='utf-8')
        
        # Parse frontmatter
        params = self._parse_frontmatter(content)
        action_type = params.get('action', 'unknown')
        action_params = params.get('parameters', {})
        
        self.logger.info(f"Executing approved action: {action_type}")
        
        # Execute based on action type
        result = {
            'file': file_path.name,
            'action': action_type,
            'timestamp': datetime.now().isoformat()
        }
        
        if action_type == 'send_email':
            result = self._execute_send_email(action_params, result)
        elif action_type == 'payment':
            result = self._execute_payment(action_params, result)
        else:
            result['status'] = 'unknown_action'
            result['message'] = f"Unknown action type: {action_type}"
        
        # Log execution
        self._log_approval('executed', action_type, action_params, 
                          result.get('status', 'unknown'))
        
        # Move to Done
        done_folder = self.vault_path / 'Done' / 'approvals'
        done_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(done_folder / file_path.name))
        
        return result
    
    def _execute_send_email(self, params: dict, result: dict) -> dict:
        """Execute send_email action via MCP."""
        try:
            # Call email MCP server
            from scripts.email_mcp_server import EmailMCPServer
            
            email_service = EmailMCPServer()
            
            email_result = email_service.send_email(
                to=params.get('to'),
                subject=params.get('subject'),
                body=params.get('body'),
                attachments=params.get('attachments'),
                html=params.get('html', False)
            )
            
            result['status'] = email_result.get('status', 'unknown')
            result['message_id'] = email_result.get('message_id')
            result['message'] = email_result.get('message', '')
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            return result
    
    def _execute_payment(self, params: dict, result: dict) -> dict:
        """Execute payment action (placeholder - implement with banking MCP)."""
        # Placeholder - in production, integrate with banking MCP
        result['status'] = 'not_implemented'
        result['message'] = 'Payment execution requires banking MCP integration'
        return result
    
    def check_expirations(self) -> list:
        """
        Check for expired approval requests.
        
        Returns:
            List of expired files moved to Rejected
        """
        expired = []
        now = datetime.now()
        
        for file_path in self.pending_approval.iterdir():
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    content = file_path.read_text(encoding='utf-8')
                    params = self._parse_frontmatter(content)
                    
                    expires_str = params.get('expires', '')
                    if expires_str:
                        expires = datetime.fromisoformat(expires_str)
                        if now > expires:
                            # Move to Rejected
                            shutil.move(
                                str(file_path),
                                str(self.rejected / file_path.name)
                            )
                            
                            # Log expiration
                            self._log_approval(
                                'expired',
                                params.get('action', 'unknown'),
                                params,
                                'rejected'
                            )
                            
                            expired.append(file_path.name)
                            self.logger.info(f"Expired approval request: {file_path.name}")
                            
                except Exception as e:
                    self.logger.warning(f"Error checking expiration: {e}")
        
        return expired
    
    def check_auto_approve(self, action_type: str, params: dict) -> bool:
        """
        Check if action qualifies for auto-approval.
        
        Args:
            action_type: Type of action
            params: Action parameters
            
        Returns:
            True if auto-approved
        """
        if action_type == 'send_email':
            # Check recipient count
            to = params.get('to', '')
            if ',' in to:
                recipients = len(to.split(','))
                if recipients > self.auto_approve_rules['email_threshold']:
                    return False
            
            # Check if to known contact
            # (implement contact list checking)
            return True
            
        elif action_type == 'payment':
            amount = params.get('amount', 0)
            if amount > self.auto_approve_rules['payment_threshold']:
                return False
            
            # Check if existing payee
            # (implement payee list checking)
            return True
        
        return False
    
    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from markdown content."""
        import re
        
        params = {}
        
        # Extract frontmatter
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            
            # Simple key-value parsing
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Try to parse as JSON for complex values
                    if value.startswith('{') or value.startswith('['):
                        try:
                            params[key] = json.loads(value)
                        except:
                            params[key] = value
                    else:
                        params[key] = value
        
        # Extract parameters JSON block
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            try:
                params['parameters'] = json.loads(json_match.group(1))
            except:
                pass
        
        return params
    
    def _log_approval(self, event: str, action_type: str, 
                      params: dict, status: str):
        """Log approval event."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'action_type': action_type,
            'actor': 'approval_workflow',
            'parameters': params,
            'status': status
        }
        
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # Append to log file
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def _safe_filename(self, text: str) -> str:
        """Create safe filename from text."""
        invalid = '<>:"/\\|？*'
        for char in invalid:
            text = text.replace(char, '_')
        return text.replace(' ', '_')
    
    def run(self):
        """Main run loop."""
        import time
        
        self.logger.info("Starting Approval Workflow monitor")
        
        try:
            while True:
                # Check for approved actions
                approved_files = list(self.approved.iterdir())
                if approved_files:
                    self.logger.info(f"Found {len(approved_files)} approved action(s)")
                    results = self.process_approved()
                    for result in results:
                        self.logger.info(f"Executed: {result.get('file')} - {result.get('status')}")
                
                # Check expirations
                expired = self.check_expirations()
                if expired:
                    self.logger.info(f"Expired {len(expired)} approval request(s)")
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("Approval Workflow stopped by user")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Approval Workflow')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--create', help='Create approval request (action:params)')
    parser.add_argument('--process', action='store_true', help='Process approved once')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    workflow = ApprovalWorkflow(vault_path)
    
    if args.create:
        # Parse action:params format
        parts = args.create.split(':', 1)
        if len(parts) == 2:
            action = parts[0]
            try:
                params = json.loads(parts[1])
            except:
                params = {'raw': parts[1]}
            
            filepath = workflow.create_approval_request(action, params)
            print(f"Created approval request: {filepath}")
        else:
            print("Usage: --create action:params")
            print("Example: --create send_email:{\"to\":\"test@example.com\"}")
        return
    
    if args.process:
        results = workflow.process_approved()
        print(f"Processed {len(results)} approved action(s)")
        for result in results:
            print(f"  {result.get('file')}: {result.get('status')}")
        return
    
    workflow.run()


if __name__ == '__main__':
    main()
