"""
LinkedIn Watcher Module

Monitors LinkedIn for new notifications, connection requests, and messages.
Uses Playwright to automate LinkedIn and detect activity.

Creates action files in /Needs_Action for Qwen Code to process.

Note: LinkedIn automation may violate LinkedIn's Terms of Service.
Use at your own risk and consider LinkedIn API for production use.

Usage:
    python linkedin_watcher.py /path/to/vault
    python linkedin_watcher.py /path/to/vault --setup  # First time setup
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

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


class LinkedInWatcher(BaseWatcher):
    """
    Watches LinkedIn for new notifications and activity.
    
    When new activity is detected, it:
    1. Extracts notification details
    2. Creates a .md action file in Needs_Action
    3. Tracks processed items to avoid duplicates
    """
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = [
        'connection request', 'message', 'job opportunity',
        'hiring', 'interview', 'position', 'role',
        'congratulations', 'work anniversary', 'promotion'
    ]
    
    # Activity types to monitor
    ACTIVITY_TYPES = [
        'connection_requests',
        'messages',
        'notifications',
        'job_alerts'
    ]
    
    def __init__(self, vault_path: str, session_path: str = None, 
                 check_interval: int = 300):
        """
        Initialize the LinkedIn watcher.
        
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
        
        super().__init__(vault_path, check_interval)
        
        # Set default session path
        default_session = Path.home() / '.linkedin_session'
        self.session_path = Path(session_path) if session_path else default_session
        
        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed item IDs
        self.load_processed_ids()
        
        self.logger.info(f"Session path: {self.session_path}")
    
    def check_for_updates(self) -> list:
        """
        Check LinkedIn for new notifications and activity.
        
        Returns:
            List of new activity items
        """
        new_items = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to LinkedIn
                try:
                    page.goto('https://www.linkedin.com', timeout=30000)
                    
                    # Wait for page to load
                    try:
                        page.wait_for_selector('.nav-item__link', timeout=15000)
                    except PlaywrightTimeout:
                        # Might need to login
                        self.logger.warning("LinkedIn not loaded. May need to login.")
                        browser.close()
                        return []
                    
                    # Wait for page stabilization
                    page.wait_for_timeout(5000)
                    
                    # Check for notifications bell
                    try:
                        # Try to click on notifications bell
                        notifications_btn = page.query_selector(
                            '.notifications-nav__item'
                        )
                        
                        if notifications_btn:
                            # Get notification count
                            badge = notifications_btn.query_selector('.artdeco-badge')
                            if badge:
                                count_text = badge.inner_text()
                                try:
                                    count = int(count_text)
                                except:
                                    count = 1
                                
                                self.logger.info(f"Found {count} unread notifications")
                                
                                # Click to see notifications
                                notifications_btn.click()
                                page.wait_for_timeout(2000)
                                
                                # Get notification items
                                notification_elements = page.query_selector_all(
                                    '.notification-item'
                                )
                                
                                for i, elem in enumerate(notification_elements[:10]):
                                    try:
                                        item_data = self._extract_notification(elem)
                                        if item_data:
                                            item_id = f"li_notif_{item_data['type']}_{item_data['title'][:30]}_{datetime.now().strftime('%Y%m%d%H')}"
                                            
                                            if item_id not in self.processed_ids:
                                                new_items.append(item_data)
                                                self.processed_ids.add(item_id)
                                    except Exception as e:
                                        self.logger.debug(f"Error extracting notification: {e}")
                                        continue
                    except Exception as e:
                        self.logger.debug(f"Could not access notifications: {e}")
                    
                    # Check for connection requests
                    try:
                        my_network_link = page.query_selector(
                            'a[href*="/mynetwork/"]'
                        )
                        if my_network_link:
                            my_network_link.click()
                            page.wait_for_timeout(3000)
                            
                            # Look for connection requests
                            pending_requests = page.query_selector_all(
                                '.invitation-card'
                            )
                            
                            for req in pending_requests[:5]:
                                try:
                                    req_data = self._extract_connection_request(req)
                                    if req_data:
                                        req_id = f"li_conn_{req_data['name']}_{datetime.now().strftime('%Y%m%d%H')}"
                                        
                                        if req_id not in self.processed_ids:
                                            new_items.append(req_data)
                                            self.processed_ids.add(req_id)
                                except Exception as e:
                                    self.logger.debug(f"Error extracting connection request: {e}")
                                    continue
                    except Exception as e:
                        self.logger.debug(f"Could not access network: {e}")
                    
                    browser.close()
                    
                except Exception as e:
                    self.logger.error(f"Error on LinkedIn: {e}")
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
            text_elem = element.query_selector('.notification-item__message')
            text = text_elem.inner_text() if text_elem else ""
            
            # Get actor name
            actor_elem = element.query_selector('.notification-item__actor')
            actor = actor_elem.inner_text() if actor_elem else "Unknown"
            
            # Determine type
            notif_type = "general"
            if "connection" in text.lower():
                notif_type = "connection"
            elif "message" in text.lower():
                notif_type = "message"
            elif "job" in text.lower() or "hiring" in text.lower():
                notif_type = "job"
            elif "congratulation" in text.lower():
                notif_type = "congratulation"
            
            return {
                'type': notif_type,
                'title': text[:100],
                'actor': actor,
                'text': text,
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.debug(f"Error extracting notification: {e}")
            return None
    
    def _extract_connection_request(self, element) -> dict:
        """Extract connection request data from element."""
        try:
            # Get name
            name_elem = element.query_selector('.invitation-card__actor-name')
            name = name_elem.inner_text() if name_elem else "Unknown"
            
            # Get headline
            headline_elem = element.query_selector('.invitation-card__subtitle')
            headline = headline_elem.inner_text() if headline_elem else ""
            
            return {
                'type': 'connection_request',
                'name': name,
                'headline': headline,
                'text': f"Connection request from {name}: {headline}",
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.debug(f"Error extracting connection request: {e}")
            return None
    
    def _get_priority(self, item: dict) -> str:
        """Determine item priority."""
        text = item.get('text', '').lower()
        item_type = item.get('type', '')
        
        # High priority types
        if item_type in ['message', 'job']:
            return 'high'
        
        # Check keywords
        for keyword in self.PRIORITY_KEYWORDS:
            if keyword in text:
                return 'high'
        
        return 'medium'
    
    def create_action_file(self, item: dict) -> Path:
        """
        Create an action file for the LinkedIn item.
        
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
type: linkedin
category: {item.get('type', 'unknown')}
received: {item['timestamp'].isoformat()}
priority: {priority}
status: pending
---

# LinkedIn Activity

## Type
{item.get('type', 'Unknown').replace('_', ' ').title()}

## Received
{item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

## Details

{item.get('text', 'No details available')}

'''
        
        # Add type-specific details
        if item.get('type') == 'connection_request':
            content += f'''
## Action Required

- [ ] Review connection request
- [ ] Accept or decline connection
- [ ] Send welcome message if accepted

## Person Details

**Name:** {item.get('name', 'Unknown')}
**Headline:** {item.get('headline', 'N/A')}
'''
        elif item.get('type') == 'message':
            content += f'''
## Action Required

- [ ] Read full message on LinkedIn
- [ ] Reply to message
- [ ] Take appropriate action
'''
        elif item.get('type') == 'job':
            content += f'''
## Action Required

- [ ] Review job opportunity
- [ ] Check if interested
- [ ] Apply or respond
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
*Created by LinkedIn Watcher*
'''
        
        filepath = self.needs_action / f'LINKEDIN_{safe_type}_{timestamp}.md'
        filepath.write_text(content, encoding='utf-8')
        
        self.logger.info(f'Created action file for LinkedIn {item.get("type", "activity")}')
        
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
        Interactive setup to create LinkedIn session.
        Opens browser for login.
        """
        print("=" * 50)
        print("LinkedIn Session Setup")
        print("=" * 50)
        print("\nA browser window will open.")
        print("Log in to your LinkedIn account.")
        print("Once logged in, close the browser window.")
        print("\nSession will be saved to:", self.session_path)
        print("\nOpening browser in 2 seconds...")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Show browser for login
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://www.linkedin.com')
            
            print("\nWaiting for you to log in...")
            print("Close the browser window when done.")
            
            # Wait for user to close browser
            try:
                while browser.is_connected():
                    page.wait_for_timeout(1000)
            except:
                pass
        
        print("\n✓ Session saved!")
        print("You can now run linkedin_watcher.py in headless mode.")
        print("\nNote: LinkedIn may require CAPTCHA or verification on automated access.")


def main():
    """Main entry point for running the LinkedIn watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--session', help='Path to session directory')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    if args.setup:
        watcher = LinkedInWatcher(vault_path, session_path=args.session)
        watcher.setup_session()
        return
    
    try:
        watcher = LinkedInWatcher(
            vault_path=vault_path,
            session_path=args.session,
            check_interval=args.interval
        )
        print(f"LinkedIn Watcher starting...")
        print(f"Vault: {vault_path}")
        print(f"Check interval: {args.interval}s ({args.interval/60:.1f} minutes)")
        print("Note: LinkedIn automation may violate ToS. Use at your own risk.")
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
