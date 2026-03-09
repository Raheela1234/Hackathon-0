"""
Facebook Watcher Module

Monitors Facebook for new notifications, messages, and page activity.
Uses Playwright to automate Facebook Web.

Note: Facebook automation may violate Facebook's Terms of Service.
Use at your own risk and consider Facebook Graph API for production use.

Usage:
    python facebook_watcher.py /path/to/vault
    python facebook_watcher.py /path/to/vault --setup  # First time setup

Environment Variables (set in .env file):
    FACEBOOK_SESSION_PATH: Path to browser session storage
    FACEBOOK_CHECK_INTERVAL: Check interval in seconds
    VAULT_PATH: Path to Obsidian vault
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Load configuration
sys.path.insert(0, str(Path(__file__).parent))
try:
    from config import get_config
    config = get_config()
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: config.py not found. Using environment variables directly.")

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")

# Import base watcher
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class FacebookWatcher(BaseWatcher):
    """
    Watches Facebook for new notifications and activity.
    
    When new activity is detected, it:
    1. Extracts notification details
    2. Creates a .md action file in Needs_Action
    3. Tracks processed items to avoid duplicates
    """
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = [
        'message', 'inbox', 'comment', 'post',
        'page like', 'follower', 'share',
        'business', 'order', 'inquiry'
    ]
    
    def __init__(self, vault_path: str = None, session_path: str = None, 
                 check_interval: int = None):
        """
        Initialize the Facebook watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Run: "
                "pip install playwright && playwright install chromium"
            )
        
        # Configuration from config module or environment or defaults
        if CONFIG_AVAILABLE:
            vault_path = vault_path or config.VAULT_PATH
            session_path = session_path or config.FACEBOOK_SESSION_PATH
            check_interval = check_interval or config.FACEBOOK_CHECK_INTERVAL
        else:
            vault_path = vault_path or os.getenv('VAULT_PATH')
            session_path = session_path or os.getenv('FACEBOOK_SESSION_PATH', str(Path.home() / '.facebook_session'))
            check_interval = check_interval or int(os.getenv('FACEBOOK_CHECK_INTERVAL', '300'))
        
        # Set default vault path if not provided
        if not vault_path:
            vault_path = str(Path(__file__).parent.parent / 'AI_Employee_Vault')
        
        super().__init__(vault_path, check_interval)
        
        # Set session path
        self.session_path = Path(session_path)
        
        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed item IDs
        self.load_processed_ids()
        
        self.logger.info(f"Session path: {self.session_path}")
    
    def check_for_updates(self) -> list:
        """
        Check Facebook for new notifications and activity.
        
        Returns:
            List of new activity items
        """
        new_items = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled'
                    ],
                    user_data_dir=str(self.session_path)
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to Facebook
                try:
                    page.goto('https://www.facebook.com', timeout=30000)
                    
                    # Wait for page to load
                    try:
                        page.wait_for_selector('[role="navigation"]', timeout=15000)
                    except PlaywrightTimeout:
                        self.logger.warning("Facebook not loaded. May need to login.")
                        browser.close()
                        return []
                    
                    # Wait for page stabilization
                    page.wait_for_timeout(5000)
                    
                    # Check for notifications
                    try:
                        # Look for notifications bell
                        notif_btn = page.query_selector(
                            '[aria-label*="Notification"]'
                        )
                        
                        if notif_btn:
                            # Check for notification badge
                            badge = notif_btn.query_selector(
                                '[class*="badge"]'
                            )
                            
                            if badge:
                                count_text = badge.inner_text()
                                try:
                                    count = int(count_text)
                                except:
                                    count = 1
                                
                                self.logger.info(f"Found {count} unread notifications")
                                
                                # Click to see notifications
                                notif_btn.click()
                                page.wait_for_timeout(2000)
                                
                                # Get notification items
                                notification_elements = page.query_selector_all(
                                    '[role="listitem"]'
                                )
                                
                                for i, elem in enumerate(notification_elements[:10]):
                                    try:
                                        item_data = self._extract_notification(elem)
                                        if item_data:
                                            item_id = f"fb_notif_{item_data['type']}_{item_data['title'][:30]}_{datetime.now().strftime('%Y%m%d%H')}"
                                            
                                            if item_id not in self.processed_ids:
                                                new_items.append(item_data)
                                                self.processed_ids.add(item_id)
                                    except Exception as e:
                                        self.logger.debug(f"Error extracting notification: {e}")
                                        continue
                    except Exception as e:
                        self.logger.debug(f"Could not access notifications: {e}")
                    
                    # Check for messages
                    try:
                        # Look for Messenger icon
                        messenger_link = page.query_selector(
                            '[aria-label*="Messenger"]'
                        )
                        
                        if messenger_link:
                            # Check for unread badge
                            msg_badge = messenger_link.query_selector(
                                '[class*="badge"]'
                            )
                            
                            if msg_badge:
                                msg_data = {
                                    'type': 'message',
                                    'title': 'New Facebook Message',
                                    'text': 'You have unread messages on Facebook Messenger',
                                    'priority': 'high',
                                    'timestamp': datetime.now()
                                }
                                
                                msg_id = f"fb_msg_{datetime.now().strftime('%Y%m%d%H')}"
                                if msg_id not in self.processed_ids:
                                    new_items.append(msg_data)
                                    self.processed_ids.add(msg_id)
                    except Exception as e:
                        self.logger.debug(f"Could not check messages: {e}")
                    
                    browser.close()
                    
                except Exception as e:
                    self.logger.error(f"Error on Facebook: {e}")
                    browser.close()
                    return []
                    
        except Exception as e:
            self.logger.error(f"Playwright error: {e}")
        
        # Save processed IDs
        self.save_processed_ids()
        
        return new_items
    
    def _extract_notification(self, element) -> dict:
        """Extract notification data from element."""
        try:
            # Get notification text
            text_elem = element.query_selector('span[dir="auto"]')
            text = text_elem.inner_text() if text_elem else ""
            
            # Determine type
            notif_type = "general"
            if "comment" in text.lower():
                notif_type = "comment"
            elif "like" in text.lower() or "react" in text.lower():
                notif_type = "reaction"
            elif "message" in text.lower():
                notif_type = "message"
            elif "post" in text.lower():
                notif_type = "post"
            elif "friend" in text.lower():
                notif_type = "friend"
            
            # Determine priority
            priority = "medium"
            if any(kw in text.lower() for kw in self.PRIORITY_KEYWORDS):
                priority = "high"
            
            return {
                'type': notif_type,
                'title': text[:100],
                'text': text,
                'priority': priority,
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.debug(f"Error extracting notification: {e}")
            return None
    
    def _get_priority(self, item: dict) -> str:
        """Determine item priority."""
        return item.get('priority', 'medium')
    
    def create_action_file(self, item: dict) -> Path:
        """
        Create an action file for the Facebook item.
        
        Args:
            item: Dict with item details
            
        Returns:
            Path to the created action file
        """
        # Determine priority
        priority = self._get_priority(item)
        
        # Create safe filename
        safe_type = self._safe_filename(item.get('type', 'unknown'))
        timestamp = item['timestamp'].strftime('%Y%m%d_%H%M%S')
        
        content = f'''---
type: facebook
category: {item.get('type', 'unknown')}
received: {item['timestamp'].isoformat()}
priority: {priority}
status: pending
---

# Facebook Activity

## Type
{item.get('type', 'Unknown').replace('_', ' ').title()}

## Received
{item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

## Details

{item.get('text', 'No details available')}

'''
        
        # Add type-specific details
        if item.get('type') == 'comment':
            content += f'''
## Action Required

- [ ] Review comment on Facebook
- [ ] Reply if needed
- [ ] Mark as complete
'''
        elif item.get('type') == 'message':
            content += f'''
## Action Required

- [ ] Read message on Facebook Messenger
- [ ] Reply to message
- [ ] Take appropriate action
'''
        elif item.get('type') == 'reaction':
            content += f'''
## Action Required

- [ ] Acknowledge the engagement
- [ ] Consider following up
- [ ] Mark as complete
'''
        else:
            content += f'''
## Action Required

- [ ] Review notification
- [ ] Take appropriate action
- [ ] Mark as complete
'''
        
        content += f'''

## Notes

<!-- Add any notes about processing this item here -->

---
*Created by Facebook Watcher*
'''
        
        filepath = self.needs_action / f'FACEBOOK_{safe_type}_{timestamp}.md'
        filepath.write_text(content, encoding='utf-8')
        
        self.logger.info(f'Created action file for Facebook {item.get("type", "activity")}')
        
        return filepath
    
    def _safe_filename(self, text: str, max_length: int = 30) -> str:
        """Create a safe filename from text."""
        # Remove invalid characters
        invalid = '<>:"/\\|？*'
        for char in invalid:
            text = text.replace(char, '_')
        
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        
        # Truncate
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def setup_session(self):
        """
        Interactive setup to create Facebook session.
        Opens browser for login.
        """
        print("=" * 50)
        print("Facebook Session Setup")
        print("=" * 50)
        print("\nA browser window will open.")
        print("Log in to your Facebook account.")
        print("Once logged in, close the browser window.")
        print("\nSession will be saved to:", self.session_path)
        print("\nOpening browser in 2 seconds...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                self.session_path,
                headless=False,  # Show browser for login
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://www.facebook.com')
            
            print("\nWaiting for you to log in...")
            print("Close the browser window when done.")
            
            # Wait for user to close browser
            try:
                while browser.is_connected():
                    page.wait_for_timeout(1000)
            except:
                pass
        
        print("\n✓ Session saved!")
        print("You can now run facebook_watcher.py in headless mode.")
        print("\nNote: Facebook automation may violate ToS. Use at your own risk.")


def main():
    """Main entry point for running the Facebook watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--session', help='Path to session directory')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    if args.setup:
        watcher = FacebookWatcher(vault_path, session_path=args.session)
        watcher.setup_session()
        return
    
    try:
        watcher = FacebookWatcher(
            vault_path=vault_path,
            session_path=args.session,
            check_interval=args.interval
        )
        print(f"Facebook Watcher starting...")
        print(f"Vault: {vault_path}")
        print(f"Check interval: {args.interval}s ({args.interval/60:.1f} minutes)")
        print("Note: Facebook automation may violate ToS. Use at your own risk.")
        watcher.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
