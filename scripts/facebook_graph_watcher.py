"""
Facebook Graph API Watcher Module

Monitors Facebook for new notifications, messages, and page activity.
Uses Facebook Graph API instead of browser automation.

Note: Requires Facebook App and Access Token.
Get credentials from: https://developers.facebook.com/apps

Usage:
    python facebook_graph_watcher.py /path/to/vault

Environment Variables (set in .env file):
    FACEBOOK_ACCESS_TOKEN: Facebook Graph API access token
    FACEBOOK_PAGE_ID: Facebook Page ID for page operations
    FACEBOOK_API_VERSION: API version (default: v19.0)
    FACEBOOK_CHECK_INTERVAL: Check interval in seconds
    VAULT_PATH: Path to Obsidian vault
"""

import os
import sys
import json
import requests
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

# Import base watcher
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class FacebookGraphWatcher(BaseWatcher):
    """
    Watches Facebook using Graph API for new notifications and activity.
    
    When new activity is detected, it:
    1. Fetches notification details from Graph API
    2. Creates a .md action file in Needs_Action
    3. Tracks processed items to avoid duplicates
    """
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = [
        'message', 'inbox', 'comment', 'post',
        'page like', 'follower', 'share',
        'business', 'order', 'inquiry'
    ]
    
    def __init__(self, vault_path: str = None, check_interval: int = None):
        """
        Initialize the Facebook Graph API watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        # Configuration from config module or environment or defaults
        if CONFIG_AVAILABLE:
            vault_path = vault_path or config.VAULT_PATH
            check_interval = check_interval or config.FACEBOOK_CHECK_INTERVAL
            self.access_token = config.FACEBOOK_ACCESS_TOKEN
            self.page_id = config.FACEBOOK_PAGE_ID
            self.api_version = config.FACEBOOK_API_VERSION
        else:
            vault_path = vault_path or os.getenv('VAULT_PATH')
            check_interval = check_interval or int(os.getenv('FACEBOOK_CHECK_INTERVAL', '300'))
            self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
            self.page_id = os.getenv('FACEBOOK_PAGE_ID', '')
            self.api_version = os.getenv('FACEBOOK_API_VERSION', 'v19.0')
        
        # Set default vault path if not provided
        if not vault_path:
            vault_path = str(Path(__file__).parent.parent / 'AI_Employee_Vault')
        
        super().__init__(vault_path, check_interval)
        
        # Graph API base URL
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
        # Verify token is configured
        if not self.access_token:
            self.logger.warning("FACEBOOK_ACCESS_TOKEN not configured. Facebook features disabled.")
        
        self.logger.info(f"Facebook API Version: {self.api_version}")
        self.logger.info(f"Page ID: {self.page_id or 'Not configured'}")
    
    def check_for_updates(self) -> list:
        """
        Check Facebook Graph API for new notifications and activity.
        
        Returns:
            List of new activity items
        """
        new_items = []
        
        if not self.access_token:
            return []
        
        try:
            # Check page notifications if page_id is configured
            if self.page_id:
                page_items = self._check_page_activity()
                new_items.extend(page_items)
            
            # Check user notifications
            user_items = self._check_user_notifications()
            new_items.extend(user_items)
            
            # Check page messages
            message_items = self._check_page_messages()
            new_items.extend(message_items)
            
        except Exception as e:
            self.logger.error(f"Error checking Facebook: {e}")
        
        return new_items
    
    def _check_page_activity(self) -> list:
        """Check page for new likes, comments, and posts."""
        items = []
        
        try:
            # Get page feed posts
            endpoint = f'{self.base_url}/{self.page_id}/feed'
            params = {
                'access_token': self.access_token,
                'limit': 10,
                'fields': 'id,message,created_time,likes.summary(true),comments.summary(true)'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            posts = data.get('data', [])
            
            for post in posts:
                post_id = post.get('id', '')
                created_time = post.get('created_time', '')
                
                # Check for new likes
                likes_count = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                if likes_count > 0:
                    item_id = f"fb_like_{post_id}_{datetime.now().strftime('%Y%m%d%H')}"
                    if item_id not in self.processed_ids:
                        items.append({
                            'type': 'like',
                            'title': f'New likes on post',
                            'text': f'Post received {likes_count} likes',
                            'post_id': post_id,
                            'likes_count': likes_count,
                            'priority': 'low',
                            'timestamp': datetime.now()
                        })
                        self.processed_ids.add(item_id)
                
                # Check for new comments
                comments_count = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                if comments_count > 0:
                    item_id = f"fb_comment_{post_id}_{datetime.now().strftime('%Y%m%d%H')}"
                    if item_id not in self.processed_ids:
                        items.append({
                            'type': 'comment',
                            'title': f'New comments on post',
                            'text': f'Post received {comments_count} comments',
                            'post_id': post_id,
                            'comments_count': comments_count,
                            'priority': 'high',
                            'timestamp': datetime.now()
                        })
                        self.processed_ids.add(item_id)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error checking page activity: {e}")
        
        return items
    
    def _check_user_notifications(self) -> list:
        """Check user notifications."""
        items = []
        
        try:
            # Get user notifications
            endpoint = f'{self.base_url}/me/notifications'
            params = {
                'access_token': self.access_token,
                'limit': 20,
                'fields': 'id,from,message,created_time,unread'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            notifications = data.get('data', [])
            
            for notif in notifications:
                if notif.get('unread', False):
                    notif_id = notif.get('id', '')
                    item_id = f"fb_notif_{notif_id}_{datetime.now().strftime('%Y%m%d%H')}"
                    
                    if item_id not in self.processed_ids:
                        # Determine type
                        notif_type = 'general'
                        message = notif.get('message', '').lower()
                        if 'comment' in message:
                            notif_type = 'comment'
                        elif 'like' in message or 'react' in message:
                            notif_type = 'reaction'
                        elif 'message' in message:
                            notif_type = 'message'
                        
                        # Determine priority
                        priority = 'medium'
                        if any(kw in message for kw in self.PRIORITY_KEYWORDS):
                            priority = 'high'
                        
                        items.append({
                            'type': notif_type,
                            'title': notif.get('from', {}).get('name', 'Unknown'),
                            'text': notif.get('message', ''),
                            'from_user': notif.get('from', {}).get('name', 'Unknown'),
                            'priority': priority,
                            'timestamp': datetime.now()
                        })
                        self.processed_ids.add(item_id)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error checking notifications: {e}")
        
        return items
    
    def _check_page_messages(self) -> list:
        """Check page inbox for new messages."""
        items = []
        
        if not self.page_id:
            return items
        
        try:
            # Get page conversations
            endpoint = f'{self.base_url}/{self.page_id}/conversations'
            params = {
                'access_token': self.access_token,
                'limit': 10,
                'fields': 'id,updated_time,messages.fields(from,message,created_time)',
                'platform': 'instagram'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('data', [])
                
                for conv in conversations:
                    messages = conv.get('messages', {}).get('data', [])
                    if messages:
                        latest_msg = messages[0]
                        from_user = latest_msg.get('from', {}).get('name', 'Unknown')
                        
                        # Check if message is from page admin (skip)
                        if from_user == 'Page':
                            continue
                        
                        msg_id = latest_msg.get('id', '')
                        item_id = f"fb_msg_{msg_id}_{datetime.now().strftime('%Y%m%d%H')}"
                        
                        if item_id not in self.processed_ids:
                            items.append({
                                'type': 'message',
                                'title': f'New message from {from_user}',
                                'text': latest_msg.get('message', ''),
                                'from_user': from_user,
                                'conversation_id': conv.get('id', ''),
                                'priority': 'high',
                                'timestamp': datetime.now()
                            })
                            self.processed_ids.add(item_id)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error checking messages: {e}")
        
        return items
    
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

- [ ] Read message on Facebook
- [ ] Reply to message
- [ ] Take appropriate action

## From
{item.get('from_user', 'Unknown')}
'''
        elif item.get('type') == 'like':
            content += f'''
## Action Required

- [ ] Acknowledge the engagement
- [ ] Consider following up
- [ ] Mark as complete

## Count
{item.get('likes_count', 0)} likes
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
*Created by Facebook Graph API Watcher*
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
    
    def post_to_page(self, message: str, link: str = None) -> dict:
        """
        Post a message to the Facebook page.
        
        Args:
            message: Message content
            link: Optional link to share
            
        Returns:
            dict with post ID
        """
        if not self.access_token or not self.page_id:
            return {'status': 'error', 'message': 'Facebook credentials not configured'}
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/feed'
            params = {
                'access_token': self.access_token,
                'message': message
            }
            
            if link:
                params['link'] = link
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Posted to Facebook. Post ID: {data.get('id')}")
            
            return {
                'status': 'success',
                'post_id': data.get('id'),
                'message': 'Post created successfully'
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error posting to Facebook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def reply_to_comment(self, comment_id: str, message: str) -> dict:
        """
        Reply to a Facebook comment.
        
        Args:
            comment_id: Comment ID to reply to
            message: Reply message
            
        Returns:
            dict with comment ID
        """
        if not self.access_token:
            return {'status': 'error', 'message': 'Facebook credentials not configured'}
        
        try:
            endpoint = f'{self.base_url}/{comment_id}/comments'
            params = {
                'access_token': self.access_token,
                'message': message
            }
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Replied to comment. Comment ID: {data.get('id')}")
            
            return {
                'status': 'success',
                'comment_id': data.get('id'),
                'message': 'Reply posted successfully'
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error replying to comment: {e}")
            return {'status': 'error', 'message': str(e)}


def main():
    """Main entry point for running the Facebook Graph API watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Graph API Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=None, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault_path if args.vault_path else str(default_vault)
    
    try:
        watcher = FacebookGraphWatcher(
            vault_path=vault_path,
            check_interval=args.interval
        )
        print(f"Facebook Graph API Watcher starting...")
        print(f"Vault: {vault_path}")
        print(f"Check interval: {watcher.check_interval}s ({watcher.check_interval/60:.1f} minutes)")
        
        if not watcher.access_token:
            print("\nWARNING: FACEBOOK_ACCESS_TOKEN not configured!")
            print("Set it in .env file or as environment variable.")
            print("Get token from: https://developers.facebook.com/apps")
        
        watcher.run()
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
