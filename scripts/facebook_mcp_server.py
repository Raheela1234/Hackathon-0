"""
Facebook Graph API MCP Server

Model Context Protocol (MCP) server for Facebook operations using Graph API.
Provides tools for Qwen Code to post updates, manage pages, and respond to comments.

Note: Requires Facebook App and Access Token.
Get credentials from: https://developers.facebook.com/apps

Usage:
    python facebook_mcp_server.py

Environment Variables (set in .env file):
    FACEBOOK_ACCESS_TOKEN: Facebook Graph API access token
    FACEBOOK_PAGE_ID: Facebook Page ID for page operations
    FACEBOOK_API_VERSION: API version (default: v19.0)
    DRY_RUN: Enable dry-run mode (true/false)
"""

import os
import sys
import json
import logging
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

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class FacebookMCPServer:
    """MCP Server for Facebook Graph API operations."""
    
    def __init__(self):
        """Initialize the Facebook MCP server."""
        # Configuration from config module or environment or defaults
        if CONFIG_AVAILABLE:
            self.access_token = config.FACEBOOK_ACCESS_TOKEN
            self.page_id = config.FACEBOOK_PAGE_ID
            self.api_version = config.FACEBOOK_API_VERSION
            self.dry_run = config.DRY_RUN
        else:
            self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
            self.page_id = os.getenv('FACEBOOK_PAGE_ID', '')
            self.api_version = os.getenv('FACEBOOK_API_VERSION', 'v19.0')
            self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('FacebookMCP')
        
        # Graph API base URL
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
        self.logger.info(f"Facebook API Version: {self.api_version}")
        self.logger.info(f"Page ID: {self.page_id or 'Not configured'}")
        self.logger.info(f"Dry run: {self.dry_run}")
    
    def post_update(self, content: str, link: str = None) -> dict:
        """
        Post an update to Facebook Page.
        
        Args:
            content: Post content
            link: Optional link to share
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would post update: {content[:50]}...")
            return {"status": "dry_run", "message": "Post not created (dry run mode)"}
        
        if not self.access_token or not self.page_id:
            return {
                "status": "error",
                "message": "Facebook credentials not configured. Set FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID."
            }
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/feed'
            params = {
                'access_token': self.access_token,
                'message': content
            }
            
            if link:
                params['link'] = link
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Posted to Facebook. Post ID: {data.get('id')}")
            
            return {
                "status": "success",
                "post_id": data.get('id'),
                "message": "Post created successfully",
                "permalink": f"https://facebook.com/{data.get('id')}"
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error posting to Facebook: {e}")
            return {"status": "error", "message": str(e)}
    
    def post_photo(self, content: str, photo_url: str) -> dict:
        """
        Post a photo to Facebook Page.
        
        Args:
            content: Caption for the photo
            photo_url: URL of the photo to post
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would post photo: {content[:50]}...")
            return {"status": "dry_run", "message": "Photo not posted (dry run mode)"}
        
        if not self.access_token or not self.page_id:
            return {
                "status": "error",
                "message": "Facebook credentials not configured"
            }
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/photos'
            params = {
                'access_token': self.access_token,
                'url': photo_url,
                'description': content
            }
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Posted photo to Facebook. Photo ID: {data.get('id')}")
            
            return {
                "status": "success",
                "photo_id": data.get('id'),
                "message": "Photo posted successfully"
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error posting photo: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_page_insights(self, metric: str = None) -> dict:
        """
        Get insights for the Facebook Page.
        
        Args:
            metric: Specific metric to fetch (optional)
            
        Returns:
            dict with page insights
        """
        if not self.access_token or not self.page_id:
            return {
                "status": "error",
                "message": "Facebook credentials not configured"
            }
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/insights'
            params = {
                'access_token': self.access_token,
                'metric': metric or 'page_impressions_unique,page_post_engagements_unique,page_fans'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse insights
            insights = {}
            for item in data.get('data', []):
                name = item.get('name')
                values = item.get('values', [])
                if values:
                    insights[name] = values[-1].get('value', 0)
            
            return {
                "status": "success",
                "page_id": self.page_id,
                "insights": insights
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting insights: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_page_posts(self, limit: int = 10) -> dict:
        """
        Get recent posts from the Facebook Page.
        
        Args:
            limit: Number of posts to retrieve
            
        Returns:
            dict with posts
        """
        if not self.access_token or not self.page_id:
            return {
                "status": "error",
                "message": "Facebook credentials not configured"
            }
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/feed'
            params = {
                'access_token': self.access_token,
                'limit': limit,
                'fields': 'id,message,created_time,likes.summary(true),comments.summary(true)'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for post in data.get('data', []):
                posts.append({
                    'id': post.get('id'),
                    'message': post.get('message', '')[:200],
                    'created_time': post.get('created_time'),
                    'likes': post.get('likes', {}).get('summary', {}).get('total_count', 0),
                    'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0)
                })
            
            return {
                "status": "success",
                "count": len(posts),
                "posts": posts
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting posts: {e}")
            return {"status": "error", "message": str(e)}
    
    def reply_to_comment(self, comment_id: str, message: str) -> dict:
        """
        Reply to a Facebook comment.
        
        Args:
            comment_id: Comment ID to reply to
            message: Reply message
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would reply to comment {comment_id}")
            return {"status": "dry_run", "message": "Reply not posted (dry run mode)"}
        
        if not self.access_token:
            return {
                "status": "error",
                "message": "Facebook credentials not configured"
            }
        
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
                "status": "success",
                "comment_id": data.get('id'),
                "message": "Reply posted successfully"
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error replying to comment: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_conversations(self, limit: int = 10) -> dict:
        """
        Get page conversations/messages.
        
        Args:
            limit: Number of conversations to retrieve
            
        Returns:
            dict with conversations
        """
        if not self.access_token or not self.page_id:
            return {
                "status": "error",
                "message": "Facebook credentials not configured"
            }
        
        try:
            endpoint = f'{self.base_url}/{self.page_id}/conversations'
            params = {
                'access_token': self.access_token,
                'limit': limit,
                'fields': 'id,updated_time,messages.limit(1).fields(from,message)'
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            conversations = []
            for conv in data.get('data', []):
                messages = conv.get('messages', {}).get('data', [])
                last_message = messages[0] if messages else {}
                
                conversations.append({
                    'id': conv.get('id'),
                    'updated_time': conv.get('updated_time'),
                    'last_message': last_message.get('message', ''),
                    'from': last_message.get('from', {}).get('name', 'Unknown')
                })
            
            return {
                "status": "success",
                "count": len(conversations),
                "conversations": conversations
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting conversations: {e}")
            return {"status": "error", "message": str(e)}


def create_mcp_server():
    """Create and run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP library not available. Running in standalone mode.")
        return None
    
    server = Server("facebook-mcp")
    facebook_service = FacebookMCPServer()
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="facebook_post_update",
                description="Post an update to Facebook Page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Post content"
                        },
                        "link": {
                            "type": "string",
                            "description": "Optional link to share"
                        }
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="facebook_post_photo",
                description="Post a photo to Facebook Page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Photo caption"
                        },
                        "photo_url": {
                            "type": "string",
                            "description": "URL of the photo"
                        }
                    },
                    "required": ["content", "photo_url"]
                }
            ),
            Tool(
                name="facebook_get_insights",
                description="Get insights for Facebook Page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Specific metric to fetch"
                        }
                    }
                }
            ),
            Tool(
                name="facebook_get_posts",
                description="Get recent posts from Facebook Page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of posts to retrieve"
                        }
                    }
                }
            ),
            Tool(
                name="facebook_reply_to_comment",
                description="Reply to a Facebook comment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "Comment ID to reply to"
                        },
                        "message": {
                            "type": "string",
                            "description": "Reply message"
                        }
                    },
                    "required": ["comment_id", "message"]
                }
            ),
            Tool(
                name="facebook_get_conversations",
                description="Get page conversations/messages",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of conversations"
                        }
                    }
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "facebook_post_update":
            result = facebook_service.post_update(
                content=arguments.get("content"),
                link=arguments.get("link")
            )
        elif name == "facebook_post_photo":
            result = facebook_service.post_photo(
                content=arguments.get("content"),
                photo_url=arguments.get("photo_url")
            )
        elif name == "facebook_get_insights":
            result = facebook_service.get_page_insights(
                metric=arguments.get("metric")
            )
        elif name == "facebook_get_posts":
            result = facebook_service.get_page_posts(
                limit=arguments.get("limit", 10)
            )
        elif name == "facebook_reply_to_comment":
            result = facebook_service.reply_to_comment(
                comment_id=arguments.get("comment_id"),
                message=arguments.get("message")
            )
        elif name == "facebook_get_conversations":
            result = facebook_service.get_conversations(
                limit=arguments.get("limit", 10)
            )
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return server


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook MCP Server (Graph API)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    
    if not MCP_AVAILABLE:
        print("MCP not available. Run in standalone mode for testing.")
        service = FacebookMCPServer()
        print("Facebook MCP Server ready (Graph API)")
        print(f"Page ID: {service.page_id or 'Not configured'}")
        print(f"Access Token: {'Configured' if service.access_token else 'Not configured'}")
        return
    
    server = create_mcp_server()
    
    if server:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
