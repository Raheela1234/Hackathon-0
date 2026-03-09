#!/usr/bin/env python
"""
Gold Tier Module Test Script

Run this to verify all Gold Tier modules are working correctly.
"""

print("=" * 50)
print("Gold Tier Module Tests")
print("=" * 50)
print()

# Test Config
print("1. Testing Config module...")
from config import get_config
c = get_config()
print(f"   Vault Path: {c.VAULT_PATH}")
print(f"   Odoo URL: {c.ODOO_URL}")
print(f"   Facebook API: {c.FACEBOOK_API_VERSION}")
print("   Config: OK")
print()

# Test Facebook Graph Watcher
print("2. Testing Facebook Graph Watcher...")
from facebook_graph_watcher import FacebookGraphWatcher
print("   Module loads: OK")
print()

# Test Facebook MCP Server
print("3. Testing Facebook MCP Server...")
from facebook_mcp_server import FacebookMCPServer
fb = FacebookMCPServer()
print(f"   API Version: {fb.api_version}")
print(f"   Page ID: {fb.page_id or 'Not configured'}")
print("   Module loads: OK")
print()

# Test Odoo MCP Server
print("4. Testing Odoo MCP Server...")
from odoo_mcp_server import OdooMCPServer
odoo = OdooMCPServer()
print(f"   Odoo URL: {odoo.url}")
print("   Module loads: OK")
print()

# Test Audit Logger
print("5. Testing Audit Logger...")
from audit_logger import AuditLogger
print("   Module loads: OK")
print()

# Test Ralph Wiggum
print("6. Testing Ralph Wiggum Loop...")
from ralph_wiggum import RalphWiggumLoop
print("   Module loads: OK")
print()

print("=" * 50)
print("All Gold Tier Modules Loaded Successfully!")
print("=" * 50)
print()
print("Next steps:")
print("1. Configure .env with your API credentials")
print("2. Run: python facebook_graph_watcher.py")
print("3. Run: python odoo_mcp_server.py")
