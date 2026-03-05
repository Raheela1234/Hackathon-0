"""
File System Watcher Module

Monitors a drop folder for new files and creates action files
for Claude Code to process. This is the simplest watcher implementation
and is perfect for the Bronze Tier hackathon deliverable.

Usage:
    python filesystem_watcher.py /path/to/vault

Or drop files in the vault's /Inbox folder to trigger processing.
"""

import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from base_watcher import BaseWatcher


class FileSystemWatcher(BaseWatcher):
    """
    Watches a drop folder for new files and creates action files.
    
    When a file is detected in the Inbox folder, it:
    1. Copies the file to Needs_Action
    2. Creates a metadata .md file describing the drop
    3. Claude Code will then process the action file
    """
    
    def __init__(self, vault_path: str, check_interval: int = 30):
        """
        Initialize the file system watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 30)
        """
        super().__init__(vault_path, check_interval)
        
        self.inbox = self.vault_path / 'Inbox'
        self.inbox.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed files
        self.load_processed_ids()
    
    def check_for_updates(self) -> list:
        """
        Check the Inbox folder for new files.
        
        Returns:
            List of file paths that need processing
        """
        new_files = []
        
        try:
            for file_path in self.inbox.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    # Create a unique ID based on file content and name
                    file_id = self._get_file_id(file_path)
                    
                    if file_id not in self.processed_ids:
                        new_files.append(file_path)
                        self.processed_ids.add(file_id)
        except Exception as e:
            self.logger.error(f'Error checking inbox: {e}')
        
        # Save processed IDs after each check
        self.save_processed_ids()
        
        return new_files
    
    def _get_file_id(self, file_path: Path) -> str:
        """
        Generate a unique ID for a file based on its content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash of file content + name
        """
        hasher = hashlib.sha256()
        hasher.update(file_path.name.encode())
        
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
        except Exception as e:
            self.logger.warning(f'Could not read file {file_path}: {e}')
            hasher.update(str(datetime.now()).encode())
        
        return hasher.hexdigest()[:16]
    
    def create_action_file(self, file_path: Path) -> Path:
        """
        Create an action file for the dropped file.
        
        Args:
            file_path: Path to the dropped file
            
        Returns:
            Path to the created action file
        """
        # Copy file to Needs_Action
        dest = self.needs_action / f'FILE_{file_path.name}'
        shutil.copy2(file_path, dest)
        
        # Create metadata file
        meta_path = self.needs_action / f'FILE_{file_path.name}.meta.md'
        
        # Get file size
        file_size = file_path.stat().st_size
        size_str = self._format_size(file_size)
        
        content = f'''---
type: file_drop
original_name: {file_path.name}
size: {file_size} ({size_str})
dropped: {datetime.now().isoformat()}
status: pending
---

# File Drop for Processing

A new file has been dropped in the Inbox folder.

## File Details

- **Original Name:** {file_path.name}
- **Size:** {size_str}
- **Dropped At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Location:** `Needs_Action/FILE_{file_path.name}`

## Suggested Actions

- [ ] Review the file content
- [ ] Determine required action
- [ ] Execute action or create plan
- [ ] Move to /Done when complete

## Notes

<!-- Add any notes about processing this file here -->

'''
        
        meta_path.write_text(content)
        
        # Remove original from inbox after processing
        try:
            file_path.unlink()
            self.logger.info(f'Removed original file from inbox: {file_path.name}')
        except Exception as e:
            self.logger.warning(f'Could not remove original file: {e}')
        
        return meta_path
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f}{unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f}TB'


def main():
    """Main entry point for running the watcher."""
    import sys
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        vault_path = default_vault
    
    watcher = FileSystemWatcher(str(vault_path), check_interval=30)
    watcher.run()


if __name__ == '__main__':
    main()
