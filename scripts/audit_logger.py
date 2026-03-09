"""
Audit Logger Module

Comprehensive audit logging for AI Employee actions.
Logs all actions to /Vault/Logs/audit/YYYY-MM-DD.json

Usage:
    from audit_logger import AuditLogger
    logger = AuditLogger(vault_path)
    logger.log_action('email_send', 'qwen_code', 'client@example.com', {'subject': 'Invoice'})
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class AuditLogger:
    """
    Comprehensive audit logging for AI Employee.
    
    Logs all actions with:
    - Timestamp
    - Action type
    - Actor (who performed the action)
    - Target (what was acted upon)
    - Parameters (details of the action)
    - Approval status
    - Result
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize audit logger.
        
        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / 'Logs' / 'audit'
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Cache for today's log file
        self._today = None
        self._log_file = None
    
    def _setup_logging(self):
        """Setup Python logging."""
        log_file = self.vault_path / 'Logs' / 'audit_logger.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AuditLogger')
    
    def _get_log_file(self) -> Path:
        """Get today's log file path."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self._today != today:
            self._today = today
            self._log_file = self.logs_dir / f'{today}.json'
            
            # Initialize file if new
            if not self._log_file.exists():
                self._log_file.write_text('[]')
        
        return self._log_file
    
    def log_action(self, action_type: str, actor: str, target: str,
                   parameters: Dict[str, Any] = None,
                   approval_status: str = 'auto',
                   approved_by: str = None,
                   result: str = 'success',
                   error_message: str = None) -> bool:
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action (email_send, payment, post, etc.)
            actor: Who performed the action (qwen_code, user, etc.)
            target: What was acted upon (email address, amount, etc.)
            parameters: Additional parameters/details
            approval_status: auto, approved, rejected, pending
            approved_by: Who approved (human, system, None)
            result: success, failure, error
            error_message: Error details if failed
            
        Returns:
            True if logged successfully
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'actor': actor,
                'target': target,
                'parameters': parameters or {},
                'approval_status': approval_status,
                'approved_by': approved_by,
                'result': result,
                'error_message': error_message
            }
            
            # Get today's log file
            log_file = self._get_log_file()
            
            # Read existing logs
            logs = json.loads(log_file.read_text())
            
            # Append new log
            logs.append(log_entry)
            
            # Write back
            log_file.write_text(json.dumps(logs, indent=2))
            
            self.logger.info(
                f"Audit: {action_type} by {actor} on {target} - {result}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
            return False
    
    def get_actions(self, date: str = None, action_type: str = None,
                    actor: str = None, result: str = None) -> list:
        """
        Query audit logs.
        
        Args:
            date: Filter by date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor
            result: Filter by result
            
        Returns:
            List of matching log entries
        """
        if date:
            log_file = self.logs_dir / f'{date}.json'
        else:
            log_file = self._get_log_file()
        
        if not log_file.exists():
            return []
        
        try:
            logs = json.loads(log_file.read_text())
            
            # Apply filters
            filtered = []
            for log in logs:
                if action_type and log.get('action_type') != action_type:
                    continue
                if actor and log.get('actor') != actor:
                    continue
                if result and log.get('result') != result:
                    continue
                filtered.append(log)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Failed to read audit log: {e}")
            return []
    
    def get_daily_summary(self, date: str = None) -> dict:
        """
        Get daily audit summary.
        
        Args:
            date: Date for summary (YYYY-MM-DD), default today
            
        Returns:
            dict with summary statistics
        """
        logs = self.get_actions(date=date)
        
        summary = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_actions': len(logs),
            'by_type': {},
            'by_actor': {},
            'by_result': {},
            'by_approval': {}
        }
        
        for log in logs:
            # Count by type
            action_type = log.get('action_type', 'unknown')
            summary['by_type'][action_type] = summary['by_type'].get(action_type, 0) + 1
            
            # Count by actor
            actor = log.get('actor', 'unknown')
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
            
            # Count by result
            result = log.get('result', 'unknown')
            summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
            
            # Count by approval status
            approval = log.get('approval_status', 'unknown')
            summary['by_approval'][approval] = summary['by_approval'].get(approval, 0) + 1
        
        return summary
    
    def export_logs(self, start_date: str, end_date: str, 
                    output_path: str) -> bool:
        """
        Export logs to a file.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_path: Path to output file
            
        Returns:
            True if exported successfully
        """
        try:
            all_logs = []
            
            # Collect logs from date range
            from datetime import timedelta
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            current = start
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                log_file = self.logs_dir / f'{date_str}.json'
                
                if log_file.exists():
                    logs = json.loads(log_file.read_text())
                    all_logs.extend(logs)
                
                current += timedelta(days=1)
            
            # Write to output file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(all_logs, f, indent=2)
            
            self.logger.info(f"Exported {len(all_logs)} logs to {output_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
            return False
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Remove old audit logs.
        
        Args:
            days_to_keep: Number of days to retain
            
        Returns:
            Number of files removed
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        removed = 0
        
        for log_file in self.logs_dir.glob('*.json'):
            # Extract date from filename
            try:
                date_str = log_file.stem  # YYYY-MM-DD
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff:
                    log_file.unlink()
                    removed += 1
                    self.logger.info(f"Removed old log: {log_file.name}")
            except Exception as e:
                self.logger.warning(f"Could not process {log_file.name}: {e}")
        
        return removed


# Global audit logger instance
_audit_logger = None


def get_audit_logger(vault_path: str) -> AuditLogger:
    """Get or create global audit logger instance."""
    global _audit_logger
    if _audit_logger is None or _audit_logger.vault_path != Path(vault_path):
        _audit_logger = AuditLogger(vault_path)
    return _audit_logger
