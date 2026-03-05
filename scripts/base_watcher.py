"""
Base Watcher Module

Abstract base class for all watcher implementations in the AI Employee system.
All watchers follow the same pattern: monitor -> detect -> create action file.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    Watchers are lightweight Python scripts that run continuously,
    monitoring various inputs and creating actionable files for
    Claude Code to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'Logs').mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
    def _setup_logging(self):
        """Configure logging to file and console."""
        log_file = self.vault_path / 'Logs' / f'watcher_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items that need processing.
        
        Returns:
            List of new items to process
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created action file
        """
        pass
    
    def run(self):
        """
        Main run loop. Continuously monitors for updates.
        
        This method runs indefinitely until interrupted.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            self.logger.info(f'Created action file: {filepath}')
                        except Exception as e:
                            self.logger.error(f'Error creating action file: {e}')
                except Exception as e:
                    self.logger.error(f'Error in check loop: {e}')
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
    
    def load_processed_ids(self):
        """Load previously processed IDs from cache file."""
        cache_file = self.vault_path / '.cache' / f'{self.__class__.__name__}_processed.txt'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.processed_ids = set(line.strip() for line in f)
    
    def save_processed_ids(self):
        """Save processed IDs to cache file."""
        cache_file = self.vault_path / '.cache' / f'{self.__class__.__name__}_processed.txt'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            for item_id in self.processed_ids:
                f.write(f'{item_id}\n')
