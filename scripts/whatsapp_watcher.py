"""
WhatsApp Watcher Module

Monitors WhatsApp Web for new messages containing priority keywords.
Uses Playwright to automate WhatsApp Web and detect unread messages.

Note: This uses WhatsApp Web automation. Be aware of WhatsApp's terms of service.
For production use, consider WhatsApp Business API.

Usage:
    python whatsapp_watcher.py /path/to/vault
"""

import os
import json
from pathlib import Path
from datetime import datetime
from base_watcher import BaseWatcher

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages with priority keywords.
    
    When a matching message is detected, it:
    1. Extracts the message content
    2. Creates a .md action file in Needs_Action
    3. Tracks processed messages to avoid duplicates
    """
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 
                         'billing', 'help', 'support', 'question', 'need']
    
    def __init__(self, vault_path: str, session_path: str = None, 
                 check_interval: int = 30):
        """
        Initialize the WhatsApp watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Run: "
                "pip install playwright && playwright install chromium"
            )
        
        super().__init__(vault_path, check_interval)
        
        # Set default session path
        default_session = Path.home() / '.whatsapp_session'
        self.session_path = Path(session_path) if session_path else default_session
        
        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed message IDs
        self.load_processed_ids()
    
    def check_for_updates(self) -> list:
        """
        Check WhatsApp Web for new messages with priority keywords.
        
        Returns:
            List of new messages (dict with text, sender, timestamp)
        """
        new_messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to WhatsApp Web
                try:
                    page.goto('https://web.whatsapp.com', timeout=30000)
                    
                    # Wait for chat list to load
                    try:
                        page.wait_for_selector('[data-testid="chat-list"]', timeout=15000)
                    except PlaywrightTimeout:
                        self.logger.warning("WhatsApp Web not loaded. May need QR scan.")
                        browser.close()
                        return []
                    
                    # Wait a bit for messages to load
                    page.wait_for_timeout(3000)
                    
                    # Find unread message indicators
                    # WhatsApp marks unread with aria-label containing "unread"
                    unread_chats = page.query_selector_all('[aria-label*="unread"]')
                    
                    for chat in unread_chats:
                        try:
                            # Get chat name/sender
                            name_elem = chat.query_selector('[dir="auto"]')
                            sender = name_elem.inner_text() if name_elem else "Unknown"
                            
                            # Get message preview text
                            msg_elem = chat.query_selector('[data-testid="chat-cell-message"]')
                            if not msg_elem:
                                msg_elem = chat.query_selector('span[dir="auto"]')
                            
                            text = msg_elem.inner_text() if msg_elem else ""
                            
                            # Check for priority keywords
                            text_lower = text.lower()
                            if any(kw in text_lower for kw in self.PRIORITY_KEYWORDS):
                                # Create unique message ID
                                msg_id = f"{sender}_{text[:20]}_{datetime.now().strftime('%Y%m%d%H%M')}"
                                
                                if msg_id not in self.processed_ids:
                                    new_messages.append({
                                        'id': msg_id,
                                        'sender': sender,
                                        'text': text,
                                        'timestamp': datetime.now()
                                    })
                                    self.processed_ids.add(msg_id)
                                    
                        except Exception as e:
                            self.logger.debug(f"Error processing chat: {e}")
                            continue
                    
                    browser.close()
                    
                except Exception as e:
                    self.logger.error(f"Error on WhatsApp Web: {e}")
                    browser.close()
                    return []
                    
        except Exception as e:
            self.logger.error(f"Playwright error: {e}")
        
        # Save processed IDs
        self.save_processed_ids()
        
        return new_messages
    
    def create_action_file(self, message: dict) -> Path:
        """
        Create an action file for the WhatsApp message.
        
        Args:
            message: Dict with sender, text, timestamp
            
        Returns:
            Path to the created action file
        """
        # Determine priority
        priority = 'high' if any(kw in message['text'].lower() 
                                for kw in ['urgent', 'emergency', 'asap']) else 'medium'
        
        # Create safe filename
        safe_sender = self._safe_filename(message['sender'])
        timestamp = message['timestamp'].strftime('%Y%m%d_%H%M%S')
        
        content = f'''---
type: whatsapp
from: {message['sender']}
received: {message['timestamp'].isoformat()}
priority: {priority}
status: pending
message_id: {message['id']}
---

# WhatsApp Message

## Sender
**From:** {message['sender']}

## Received
{message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

## Message Content

{message['text']}

## Suggested Actions

- [ ] Reply via WhatsApp
- [ ] Take appropriate action
- [ ] Mark as complete

## Notes

<!-- Add any notes about processing this message here -->

---
*Created by WhatsApp Watcher*
'''
        
        filepath = self.needs_action / f'WHATSAPP_{safe_sender}_{timestamp}.md'
        filepath.write_text(content, encoding='utf-8')
        
        self.logger.info(f'Created action file for message from {message["sender"]}')
        
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
        Interactive setup to create WhatsApp session.
        Opens browser for QR code scanning.
        """
        print("=" * 50)
        print("WhatsApp Session Setup")
        print("=" * 50)
        print("\nA browser window will open.")
        print("Scan the QR code with your WhatsApp mobile app.")
        print("Once logged in, close the browser window.")
        print("\nSession will be saved to:", self.session_path)
        print("\nPress Enter to continue...")
        input()
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                self.session_path,
                headless=False,  # Show browser for QR scan
                args=['--start-maximized']
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://web.whatsapp.com')
            
            print("\nWaiting for you to scan QR code and log in...")
            print("Close the browser window when done.")
            
            # Wait for user to close browser
            try:
                while browser.is_connected():
                    page.wait_for_timeout(1000)
            except:
                pass
        
        print("\n✓ Session saved!")
        print("You can now run whatsapp_watcher.py in headless mode.")


def main():
    """Main entry point for running the WhatsApp watcher."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--session', help='Path to session directory')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    if args.setup:
        watcher = WhatsAppWatcher(vault_path, session_path=args.session)
        watcher.setup_session()
        return
    
    try:
        watcher = WhatsAppWatcher(
            vault_path=vault_path,
            session_path=args.session,
            check_interval=args.interval
        )
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
