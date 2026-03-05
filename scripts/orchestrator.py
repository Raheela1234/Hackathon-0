"""
Orchestrator Module

Master process for the AI Employee system. Monitors the Needs_Action folder
and triggers Qwen Code to process pending items. Also handles Dashboard
updates and coordinates between watchers and the reasoning engine.

Usage:
    python orchestrator.py /path/to/vault

Or for one-time processing:
    python orchestrator.py /path/to/vault --once
"""

import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


class Orchestrator:
    """
    Main orchestrator for the AI Employee system.

    Responsibilities:
    - Monitor Needs_Action folder for pending items
    - Trigger Qwen Code to process items
    - Update Dashboard.md with current status
    - Move completed items to Done folder
    - Log all activities
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the orchestrator.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        
        # Define folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        self.handbook = self.vault_path / 'Company_Handbook.md'
        
        # Ensure directories exist
        for folder in [self.needs_action, self.done, self.plans, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processing state
        self.processed_count = 0
        self.error_count = 0
        
    def _setup_logging(self):
        """Configure logging to file and console."""
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')
    
    def get_pending_items(self) -> list:
        """
        Get list of pending action files in Needs_Action folder.
        
        Returns:
            List of Path objects for pending files
        """
        pending = []
        
        try:
            for file_path in self.needs_action.iterdir():
                if file_path.is_file():
                    # Skip meta files, process all other files
                    if not file_path.name.endswith('.meta.md'):
                        pending.append(file_path)
        except Exception as e:
            self.logger.error(f'Error checking Needs_Action: {e}')
        
        return pending
    
    def process_item(self, file_path: Path) -> bool:
        """
        Process a single action file using Claude Code.
        
        Args:
            file_path: Path to the action file to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        self.logger.info(f'Processing: {file_path.name}')
        
        try:
            # Read the action file to understand what needs to be done
            content = file_path.read_text()
            
            # Create a plan file for this item
            plan_file = self.plans / f'PLAN_{file_path.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            plan_content = f'''---
created: {datetime.now().isoformat()}
source: {file_path.name}
status: in_progress
---

# Plan for: {file_path.name}

## Objective
<!-- Qwen Code will fill this in -->

## Steps
- [ ] Analyze the request
- [ ] Determine required actions
- [ ] Execute or request approval
- [ ] Document completion

## Notes
<!-- Processing started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
'''
            plan_file.write_text(plan_content)

            # Build the Qwen Code prompt
            prompt = f'''You are an AI Employee assistant. Process the following task file.

File: {file_path.name}
Location: {self.needs_action}

Read the Company Handbook at {self.handbook} for rules and guidelines.

Current task file content:
{content}

Your responsibilities:
1. Analyze what action is needed
2. Check the Company Handbook for any rules that apply
3. Create or update the plan file: {plan_file}
4. If the task requires approval, create a file in /Pending_Approval/
5. If the task can be completed autonomously, do so and document it
6. When complete, move the task file to /Done/ and update the plan

Be helpful, follow the handbook rules, and ask for clarification if needed.'''

            # Check if Qwen Code is available
            if not self._check_qwen_available():
                self.logger.warning('Qwen Code not available, skipping processing')
                return False

            # Run Qwen Code with the prompt
            self.logger.info('Invoking Qwen Code...')

            result = subprocess.run(
                ['qwen', '--prompt', prompt],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=True  # On Windows, use shell=True to find npm-installed commands
            )

            # Log the output
            if result.stdout:
                self.logger.info(f'Qwen output: {result.stdout[:500]}...')
            if result.stderr:
                self.logger.warning(f'Qwen stderr: {result.stderr}')

            # Update plan with completion status
            if result.returncode == 0:
                plan_content = plan_file.read_text()
                plan_content = plan_content.replace(
                    'status: in_progress',
                    'status: completed'
                )
                plan_content += f'\n\n## Completed\nTask processed at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                plan_file.write_text(plan_content)

                # Move to Done
                self._move_to_done(file_path)
                self.processed_count += 1
                self.logger.info(f'Completed: {file_path.name}')
                return True
            else:
                self.error_count += 1
                self.logger.error(f'Qwen failed with code {result.returncode}')
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f'Timeout processing {file_path.name}')
            self.error_count += 1
            return False
        except Exception as e:
            self.logger.error(f'Error processing {file_path.name}: {e}')
            self.error_count += 1
            return False
    
    def _move_to_done(self, file_path: Path):
        """Move a processed file to the Done folder."""
        try:
            dest = self.done / file_path.name
            shutil.move(str(file_path), str(dest))
            
            # Also move any associated meta file
            meta_file = file_path.with_name(file_path.stem + '.meta.md')
            if meta_file.exists():
                shutil.move(str(meta_file), str(self.done / meta_file.name))
                
        except Exception as e:
            self.logger.error(f'Error moving {file_path.name} to Done: {e}')
    
    def _check_qwen_available(self) -> bool:
        """Check if Qwen Code is installed and available."""
        try:
            # On Windows, use shell=True to find npm-installed commands
            result = subprocess.run(
                ['qwen', '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        try:
            pending = self.get_pending_items()
            pending_count = len(pending)
            
            # Count items in Done folder
            done_count = len(list(self.done.iterdir())) if self.done.exists() else 0
            
            # Get recent activity from logs
            recent_activity = self._get_recent_activity()
            
            if self.dashboard.exists():
                content = self.dashboard.read_text()
                
                # Update the status section
                content = self._update_dashboard_field(
                    content, 'Pending Actions', str(pending_count)
                )
                content = self._update_dashboard_field(
                    content, 'Completed Today', str(self.processed_count)
                )
                content = self._update_dashboard_field(
                    content, 'Last Activity', datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                # Update recent activity section
                if recent_activity:
                    activity_section = '\n## Recent Activity\n\n'
                    for activity in recent_activity[:5]:  # Last 5 items
                        activity_section += f'- {activity}\n'
                    
                    if '## Recent Activity' in content:
                        # Replace existing section
                        start = content.find('## Recent Activity')
                        end = content.find('##', start + 1)
                        if end == -1:
                            end = len(content)
                        content = content[:start] + activity_section + content[end:]
                    else:
                        content += activity_section
                
                self.dashboard.write_text(content)
                self.logger.info('Dashboard updated')
                
        except Exception as e:
            self.logger.error(f'Error updating dashboard: {e}')
    
    def _update_dashboard_field(self, content: str, field: str, value: str) -> str:
        """Update a specific field in the dashboard table."""
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            if field in line and '|' in line:
                # This is the row to update
                parts = line.split('|')
                if len(parts) >= 3:
                    parts[2] = f' {value} '
                    line = '|'.join(parts)
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _get_recent_activity(self) -> list:
        """Get recent activity from the logs."""
        activities = []
        
        try:
            # Look for today's log file
            today_log = self.logs / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'
            
            if today_log.exists():
                with open(today_log, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines[-20:]:  # Last 20 lines
                    if 'INFO' in line:
                        # Extract the message
                        parts = line.split(' - ')
                        if len(parts) >= 4:
                            activities.append(parts[-1].strip())
        except Exception as e:
            self.logger.error(f'Error getting recent activity: {e}')
        
        return activities
    
    def run(self):
        """Main run loop for the orchestrator."""
        self.logger.info('=' * 50)
        self.logger.info('AI Employee Orchestrator Starting')
        self.logger.info(f'Vault: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info('=' * 50)

        # Check Qwen availability
        if not self._check_qwen_available():
            self.logger.warning('Qwen Code not found. Install and configure Qwen Code.')
            self.logger.warning('Continuing in monitoring mode only...')
        
        try:
            while True:
                # Update dashboard
                self.update_dashboard()
                
                # Process pending items
                pending = self.get_pending_items()
                
                if pending:
                    self.logger.info(f'Found {len(pending)} pending item(s)')
                    
                    for item in pending:
                        self.process_item(item)
                else:
                    self.logger.debug('No pending items')
                
                # Wait for next check
                import time
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
    
    def run_once(self):
        """Process all pending items once and exit."""
        self.logger.info('Running one-time processing...')
        
        self.update_dashboard()
        pending = self.get_pending_items()
        
        if not pending:
            self.logger.info('No pending items')
            return
        
        self.logger.info(f'Processing {len(pending)} item(s)')
        
        for item in pending:
            self.process_item(item)
        
        self.update_dashboard()
        self.logger.info(f'Processing complete. Success: {self.processed_count}, Errors: {self.error_count}')


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--once', action='store_true', help='Process once and exit')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    orchestrator = Orchestrator(vault_path, check_interval=args.interval)
    
    if args.status:
        pending = orchestrator.get_pending_items()
        print(f'Pending items: {len(pending)}')
        for item in pending:
            print(f'  - {item.name}')
        return
    
    if args.once:
        orchestrator.run_once()
    else:
        orchestrator.run()


if __name__ == '__main__':
    main()
