"""
Scheduling Utility

Automated scheduling for AI Employee tasks via cron (Linux/Mac) or 
Task Scheduler (Windows). Supports daily briefings, weekly audits,
and custom scheduled Qwen Code prompts.

Usage:
    # Windows
    python scheduler.py register --task daily_briefing --time "08:00"
    python scheduler.py list
    python scheduler.py remove --task daily_briefing
    
    # Linux/Mac
    python scheduler.py install
    
    # Run task manually
    python scheduler.py run daily_briefing
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


class Scheduler:
    """
    Manages scheduled tasks for AI Employee.
    
    Supports:
    - Windows Task Scheduler
    - Linux/Mac cron
    - Manual task execution
    """
    
    # Pre-built task definitions
    TASKS = {
        'daily_briefing': {
            'description': 'Generate daily business briefing',
            'schedule': '0 8 * * *',  # 8:00 AM daily
            'prompt': '''Generate a daily briefing based on:
1. Tasks completed yesterday (check /Done folder)
2. Pending items in /Needs_Action
3. Upcoming deadlines from /Business_Goals.md

Output to: /Briefings/{date}_Daily_Briefing.md'''
        },
        'weekly_audit': {
            'description': 'Weekly business audit and revenue report',
            'schedule': '0 22 * * 0',  # 10:00 PM Sunday
            'prompt': '''Generate a weekly business audit:
1. Revenue from /Accounting folder this week
2. Completed tasks from /Done
3. Bottlenecks identified
4. Subscription audit (check for unused services)

Output to: /Briefings/{date}_Weekly_Audit.md'''
        },
        'process_inbox': {
            'description': 'Process all pending inbox items',
            'schedule': '0 */2 * * *',  # Every 2 hours
            'prompt': '''Process all files in /Needs_Action:
1. Read each file
2. Determine required action
3. Execute or create approval request
4. Move completed to /Done

Update Dashboard.md with results.'''
        }
    }
    
    def __init__(self, vault_path: str = None):
        """
        Initialize scheduler.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        # Default vault path
        default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
        self.vault_path = Path(vault_path) if vault_path else default_vault
        
        # Config file
        self.config_file = Path(__file__).parent / 'scheduled_tasks.json'
        
        # Load custom tasks
        self.custom_tasks = self._load_custom_tasks()
        
        # Detect OS
        self.is_windows = os.name == 'nt'
    
    def _load_custom_tasks(self) -> dict:
        """Load custom tasks from config file."""
        if self.config_file.exists():
            try:
                config = json.loads(self.config_file.read_text())
                return {t['name']: t for t in config.get('tasks', [])}
            except Exception as e:
                print(f"Warning: Could not load custom tasks: {e}")
        return {}
    
    def get_all_tasks(self) -> dict:
        """Get all available tasks (built-in + custom)."""
        all_tasks = dict(self.TASKS)
        all_tasks.update(self.custom_tasks)
        return all_tasks
    
    def run_task(self, task_name: str) -> dict:
        """
        Run a scheduled task manually.
        
        Args:
            task_name: Name of task to run
            
        Returns:
            Task execution result
        """
        all_tasks = self.get_all_tasks()
        
        if task_name not in all_tasks:
            return {
                'status': 'error',
                'message': f"Unknown task: {task_name}"
            }
        
        task = all_tasks[task_name]
        prompt = task.get('prompt', '')
        
        # Replace date placeholder
        date_str = datetime.now().strftime('%Y-%m-%d')
        prompt = prompt.replace('{date}', date_str)
        
        print(f"Running task: {task_name}")
        print(f"Description: {task.get('description', 'N/A')}")
        print("-" * 50)
        
        # Run Qwen Code with the prompt
        try:
            result = subprocess.run(
                ['qwen', '--prompt', prompt],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=300,
                shell=self.is_windows
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'task': task_name,
                    'output': result.stdout[:500] if result.stdout else 'Task completed'
                }
            else:
                return {
                    'status': 'error',
                    'task': task_name,
                    'error': result.stderr or f"Exit code: {result.returncode}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'task': task_name,
                'error': 'Task timed out (5 minute limit)'
            }
        except FileNotFoundError:
            return {
                'status': 'error',
                'task': task_name,
                'error': 'Qwen Code not found. Ensure it is installed and in PATH.'
            }
        except Exception as e:
            return {
                'status': 'error',
                'task': task_name,
                'error': str(e)
            }
    
    def register_task(self, task_name: str, time_str: str = None) -> dict:
        """
        Register a task with the system scheduler.
        
        Args:
            task_name: Name of task to register
            time_str: Time in HH:MM format (for Windows)
            
        Returns:
            Registration result
        """
        all_tasks = self.get_all_tasks()
        
        if task_name not in all_tasks:
            return {'status': 'error', 'message': f"Unknown task: {task_name}"}
        
        task = all_tasks[task_name]
        
        if self.is_windows:
            return self._register_windows(task_name, task, time_str)
        else:
            return self._register_cron(task_name, task)
    
    def _register_windows(self, task_name: str, task: dict, time_str: str) -> dict:
        """Register task with Windows Task Scheduler."""
        if not time_str:
            time_str = "08:00"  # Default to 8 AM
        
        # Parse time
        try:
            hour, minute = time_str.split(':')
            hour = int(hour)
            minute = int(minute)
        except:
            return {'status': 'error', 'message': 'Invalid time format. Use HH:MM'}
        
        # Build command
        script_path = Path(__file__).absolute()
        python_path = sys.executable
        
        cmd = f'"{python_path}" "{script_path}" run {task_name}'
        
        # Create scheduled task using schtasks
        schtasks_cmd = [
            'schtasks', '/Create',
            '/TN', f'AI_Employee_{task_name}',
            '/TR', cmd,
            '/SC', 'DAILY',
            '/ST', f'{hour:02d}:{minute:02d}',
            '/RL', 'HIGHEST',
            '/F'  # Force overwrite if exists
        ]
        
        try:
            result = subprocess.run(schtasks_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'message': f"Task '{task_name}' registered to run daily at {time_str}"
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Failed to register task'
                }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _register_cron(self, task_name: str, task: dict) -> dict:
        """Register task with cron."""
        script_path = Path(__file__).absolute()
        python_path = sys.executable
        
        # Get cron schedule
        schedule = task.get('schedule', '0 8 * * *')
        
        cron_line = f"{schedule} {python_path} {script_path} run {task_name}\n"
        
        print(f"To register this task, add the following to your crontab:")
        print(f"  {cron_line}")
        print(f"\nRun: crontab -e")
        
        return {
            'status': 'info',
            'message': 'Manual cron registration required',
            'cron_line': cron_line
        }
    
    def list_registered(self) -> list:
        """List registered scheduled tasks."""
        if self.is_windows:
            return self._list_windows_tasks()
        else:
            return self._list_cron_tasks()
    
    def _list_windows_tasks(self) -> list:
        """List AI Employee tasks in Windows Task Scheduler."""
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/FO', 'TABLE'],
                capture_output=True,
                text=True
            )
            
            tasks = []
            for line in result.stdout.split('\n'):
                if 'AI_Employee_' in line:
                    tasks.append(line.strip())
            
            return tasks
        except:
            return []
    
    def _list_cron_tasks(self) -> list:
        """List AI Employee tasks in crontab."""
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True
            )
            
            tasks = []
            for line in result.stdout.split('\n'):
                if 'scheduler.py run' in line:
                    tasks.append(line.strip())
            
            return tasks
        except:
            return []
    
    def remove_task(self, task_name: str) -> dict:
        """
        Remove a scheduled task.
        
        Args:
            task_name: Name of task to remove
            
        Returns:
            Removal result
        """
        if self.is_windows:
            try:
                result = subprocess.run(
                    ['schtasks', '/Delete', '/TN', f'AI_Employee_{task_name}', '/F'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {'status': 'success', 'message': f"Task '{task_name}' removed"}
                else:
                    return {'status': 'error', 'message': 'Task not found or removal failed'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return {
                'status': 'info',
                'message': 'Remove manually from crontab: crontab -e'
            }
    
    def install_cron(self) -> dict:
        """Install all tasks to crontab (Linux/Mac)."""
        script_path = Path(__file__).absolute()
        python_path = sys.executable
        
        # Build cron entries
        cron_entries = []
        for task_name, task in self.TASKS.items():
            schedule = task.get('schedule', '0 8 * * *')
            cron_entries.append(
                f"{schedule} {python_path} {script_path} run {task_name}"
            )
        
        cron_content = '\n'.join(cron_entries) + '\n'
        
        print("Cron entries to install:")
        print("-" * 50)
        print(cron_content)
        print("-" * 50)
        print("\nTo install automatically, run:")
        print(f"  (crontab -l 2>/dev/null; echo '{cron_content}') | crontab -")
        
        return {
            'status': 'info',
            'entries': cron_entries
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Scheduler')
    parser.add_argument('command', choices=['run', 'register', 'list', 'remove', 'install'],
                       help='Command to execute')
    parser.add_argument('--task', help='Task name')
    parser.add_argument('--time', help='Time in HH:MM format (Windows)')
    parser.add_argument('--vault', help='Path to Obsidian vault')
    
    args = parser.parse_args()
    
    scheduler = Scheduler(args.vault)
    
    if args.command == 'run':
        if not args.task:
            print("Error: --task required")
            return
        result = scheduler.run_task(args.task)
        print(f"Status: {result.get('status')}")
        if result.get('output'):
            print(f"Output: {result['output']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    elif args.command == 'register':
        if not args.task:
            print("Error: --task required")
            return
        result = scheduler.register_task(args.task, args.time)
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
    
    elif args.command == 'list':
        tasks = scheduler.list_registered()
        if tasks:
            print("Registered tasks:")
            for task in tasks:
                print(f"  {task}")
        else:
            print("No registered tasks found")
    
    elif args.command == 'remove':
        if not args.task:
            print("Error: --task required")
            return
        result = scheduler.remove_task(args.task)
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
    
    elif args.command == 'install':
        result = scheduler.install_cron()
        print(f"Status: {result.get('status')}")


if __name__ == '__main__':
    main()
