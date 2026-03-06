"""
LinkedIn MCP Server

Model Context Protocol (MCP) server for LinkedIn operations.
Provides tools for Qwen Code to post updates, send messages, and manage connections.

Uses Playwright for browser automation.

Note: LinkedIn automation may violate LinkedIn's Terms of Service.
Use at your own risk and consider LinkedIn API for production use.

Usage:
    python linkedin_mcp_server.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class LinkedInMCPServer:
    """MCP Server for LinkedIn operations."""
    
    def __init__(self, session_path: str = None):
        """Initialize the LinkedIn MCP server."""
        # Set default session path
        default_session = Path.home() / '.linkedin_session'
        self.session_path = Path(session_path) if session_path else default_session
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('LinkedInMCP')
        
        # Dry run mode
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"Dry run mode: {self.dry_run}")
    
    def post_update(self, content: str, visibility: str = 'public') -> dict:
        """
        Post an update to LinkedIn.
        
        Args:
            content: Post content (max 3000 characters)
            visibility: 'public', 'connections', or 'group'
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would post update: {content[:50]}...")
            return {"status": "dry_run", "message": "Post not created (dry run mode)"}
        
        try:
            with sync_playwright() as p:
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
                
                # Navigate to LinkedIn
                page.goto('https://www.linkedin.com', timeout=30000)
                page.wait_for_timeout(5000)
                
                # Check if logged in
                if 'login' in page.url.lower():
                    browser.close()
                    return {
                        "status": "error",
                        "message": "Not logged in. Run setup first."
                    }
                
                # Find and click the post creation box
                try:
                    # Click on "Start a post"
                    post_trigger = page.query_selector(
                        'button[aria-label="Start a post"]'
                    )
                    if not post_trigger:
                        # Alternative selector
                        post_trigger = page.query_selector(
                            '.share-box-feed-entry__trigger'
                        )
                    
                    if post_trigger:
                        post_trigger.click()
                        page.wait_for_timeout(2000)
                        
                        # Find the text editor and type content
                        editor = page.query_selector(
                            '.ql-editor.text-input'
                        )
                        
                        if editor:
                            editor.fill(content[:3000])  # LinkedIn limit
                            page.wait_for_timeout(1000)
                            
                            # Set visibility if needed
                            if visibility != 'public':
                                visibility_btn = page.query_selector(
                                    '[aria-label*="visibility"]'
                                )
                                if visibility_btn:
                                    visibility_btn.click()
                                    page.wait_for_timeout(1000)
                                    # Select appropriate visibility option
                                    # (implementation depends on LinkedIn UI)
                            
                            # Click Post button
                            post_btn = page.query_selector(
                                'button[aria-label="Post"]'
                            )
                            if post_btn:
                                post_btn.click()
                                page.wait_for_timeout(3000)
                                
                                self.logger.info("LinkedIn post created successfully")
                                
                                browser.close()
                                return {
                                    "status": "success",
                                    "message": "Post created successfully",
                                    "content_length": len(content)
                                }
                            else:
                                browser.close()
                                return {
                                    "status": "error",
                                    "message": "Post button not found"
                                }
                        else:
                            browser.close()
                            return {
                                "status": "error",
                                "message": "Editor not found"
                            }
                    else:
                        browser.close()
                        return {
                            "status": "error",
                            "message": "Post trigger not found"
                        }
                        
                except Exception as e:
                    browser.close()
                    return {
                        "status": "error",
                        "message": str(e)
                    }
                    
        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}")
            return {"status": "error", "message": str(e)}
    
    def accept_connection(self, profile_name: str) -> dict:
        """
        Accept a connection request.
        
        Args:
            profile_name: Name of the person whose request to accept
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would accept connection from {profile_name}")
            return {"status": "dry_run", "message": "Connection not accepted (dry run mode)"}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox']
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://www.linkedin.com/mynetwork/', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Find connection request by name
                invitations = page.query_selector_all('.invitation-card')
                
                for invite in invitations:
                    name_elem = invite.query_selector('.invitation-card__actor-name')
                    if name_elem and profile_name.lower() in name_elem.inner_text().lower():
                        # Find and click accept button
                        accept_btn = invite.query_selector(
                            'button[aria-label="Accept"]'
                        )
                        if accept_btn:
                            accept_btn.click()
                            page.wait_for_timeout(1000)
                            
                            self.logger.info(f"Accepted connection from {profile_name}")
                            
                            browser.close()
                            return {
                                "status": "success",
                                "message": f"Accepted connection from {profile_name}"
                            }
                
                browser.close()
                return {
                    "status": "not_found",
                    "message": f"Connection request from {profile_name} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_message(self, recipient_name: str, message: str) -> dict:
        """
        Send a message to a connection.
        
        Args:
            recipient_name: Name of the recipient
            message: Message content
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would send message to {recipient_name}")
            return {"status": "dry_run", "message": "Message not sent (dry run mode)"}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox']
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Go to messaging
                page.goto('https://www.linkedin.com/messaging/', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Search for recipient
                search_box = page.query_selector('input[aria-label="Search messages"]')
                if search_box:
                    search_box.fill(recipient_name)
                    page.wait_for_timeout(2000)
                    
                    # Click on the recipient
                    result = page.query_selector('.msg-search-results li')
                    if result:
                        result.click()
                        page.wait_for_timeout(2000)
                        
                        # Type and send message
                        message_box = page.query_selector(
                            '.msg-form__contenteditable'
                        )
                        if message_box:
                            message_box.fill(message)
                            page.wait_for_timeout(1000)
                            
                            send_btn = page.query_selector(
                                'button[aria-label="Send message"]'
                            )
                            if send_btn:
                                send_btn.click()
                                page.wait_for_timeout(1000)
                                
                                self.logger.info(f"Message sent to {recipient_name}")
                                
                                browser.close()
                                return {
                                    "status": "success",
                                    "message": f"Message sent to {recipient_name}"
                                }
                
                browser.close()
                return {
                    "status": "error",
                    "message": f"Could not send message to {recipient_name}"
                }
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_profile_url(self) -> str:
        """Get the current user's profile URL."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox']
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://www.linkedin.com/mynetwork/', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Get profile link
                profile_link = page.query_selector('a[href*="/in/"]')
                if profile_link:
                    href = profile_link.get_attribute('href')
                    browser.close()
                    return href
                
                browser.close()
                return "unknown"
        except:
            return "unknown"


def create_mcp_server():
    """Create and run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP library not available. Running in standalone mode.")
        return None
    
    server = Server("linkedin-mcp")
    linkedin_service = LinkedInMCPServer()
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="post_update",
                description="Post an update to LinkedIn",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Post content (max 3000 characters)"
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "connections", "group"],
                            "description": "Post visibility"
                        }
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="accept_connection",
                description="Accept a LinkedIn connection request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "profile_name": {
                            "type": "string",
                            "description": "Name of the person"
                        }
                    },
                    "required": ["profile_name"]
                }
            ),
            Tool(
                name="send_message",
                description="Send a message to a LinkedIn connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "recipient_name": {
                            "type": "string",
                            "description": "Name of the recipient"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message content"
                        }
                    },
                    "required": ["recipient_name", "message"]
                }
            ),
            Tool(
                name="get_profile_url",
                description="Get the current user's LinkedIn profile URL",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "post_update":
            result = linkedin_service.post_update(
                content=arguments.get("content"),
                visibility=arguments.get("visibility", "public")
            )
        elif name == "accept_connection":
            result = linkedin_service.accept_connection(
                profile_name=arguments.get("profile_name")
            )
        elif name == "send_message":
            result = linkedin_service.send_message(
                recipient_name=arguments.get("recipient_name"),
                message=arguments.get("message")
            )
        elif name == "get_profile_url":
            url = linkedin_service.get_profile_url()
            result = {"status": "success", "profile_url": url}
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return server


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn MCP Server')
    parser.add_argument('--session', help='Path to session directory')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    
    if not MCP_AVAILABLE:
        print("MCP not available. Run in standalone mode for testing.")
        linkedin_service = LinkedInMCPServer(args.session)
        print("LinkedIn MCP Server ready (standalone mode)")
        print("Available actions: post_update, accept_connection, send_message")
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
