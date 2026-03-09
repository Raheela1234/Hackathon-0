"""
Odoo MCP Server

Model Context Protocol (MCP) server for Odoo ERP integration.
Provides tools for Qwen Code to manage accounting, invoices, customers, and products.

Uses Odoo 19+ JSON-RPC API.

Usage:
    python odoo_mcp_server.py
    
Environment Variables (set in .env file):
    ODOO_URL: Odoo server URL (default: http://localhost:8069)
    ODOO_DB: Database name (default: odoo)
    ODOO_USERNAME: Admin username (default: admin)
    ODOO_PASSWORD: Admin password (default: admin)
    ODOO_MASTER_PASSWORD: Master password for database operations
    DRY_RUN: Enable dry-run mode (true/false)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Load configuration
sys.path.insert(0, str(Path(__file__).parent))
try:
    from config import get_config
    config = get_config()
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: config.py not found. Using environment variables directly.")

# Odoo API imports
try:
    import xmlrpc.client
    import requests
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False
    print("Odoo dependencies not installed. Run: pip install xmlrpc3 requests")

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class OdooMCPServer:
    """MCP Server for Odoo ERP operations."""
    
    def __init__(self, url: str = None, db: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize the Odoo MCP server.
        
        Args:
            url: Odoo server URL
            db: Database name
            username: Admin username
            password: Admin password
        """
        # Configuration from config module or environment or defaults
        if CONFIG_AVAILABLE:
            self.url = url or config.ODOO_URL
            self.db = db or config.ODOO_DB
            self.username = username or config.ODOO_USERNAME
            self.password = password or config.ODOO_PASSWORD
            self.dry_run = config.DRY_RUN
        else:
            self.url = url or os.getenv('ODOO_URL', 'http://localhost:8069')
            self.db = db or os.getenv('ODOO_DB', 'odoo')
            self.username = username or os.getenv('ODOO_USERNAME', 'admin')
            self.password = password or os.getenv('ODOO_PASSWORD', 'admin')
            self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('OdooMCP')

        # Initialize Odoo connection
        self.uid = None
        self.common = None
        self.models = None

        if ODOO_AVAILABLE:
            self._connect()

        self.logger.info(f"Odoo URL: {self.url}")
        self.logger.info(f"Database: {self.db}")
        self.logger.info(f"Dry run: {self.dry_run}")
    
    def _connect(self):
        """Connect to Odoo server."""
        try:
            # Common endpoint for authentication
            self.common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common'
            )
            
            # Models endpoint for data operations
            self.models = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/object',
                use_builtin_types=True
            )
            
            # Authenticate
            self.uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )
            
            if self.uid:
                self.logger.info(f"Connected to Odoo. User ID: {self.uid}")
            else:
                self.logger.error("Odoo authentication failed. Check credentials.")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Odoo: {e}")
    
    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model."""
        if not self.uid:
            raise Exception("Not connected to Odoo")
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )
    
    # ==================== Accounting ====================
    
    def get_invoices(self, limit: int = 10, state: str = None) -> dict:
        """
        Get list of invoices.
        
        Args:
            limit: Maximum number of invoices
            state: Filter by state (draft, posted, cancel)
            
        Returns:
            dict with list of invoices
        """
        try:
            domain = []
            if state:
                domain.append(('state', '=', state))
            
            invoices = self._execute(
                'account.move',
                'search_read',
                domain=domain,
                fields=['name', 'partner_id', 'amount_total', 'amount_due', 
                       'invoice_date', 'state', 'move_type'],
                limit=limit
            )
            
            return {
                "status": "success",
                "count": len(invoices),
                "invoices": invoices
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_invoice(self, partner_id: int, amount: float, 
                       description: str, invoice_type: str = 'out_invoice') -> dict:
        """
        Create a new customer invoice.
        
        Args:
            partner_id: Customer ID
            amount: Invoice amount
            description: Invoice description
            invoice_type: Type of invoice
            
        Returns:
            dict with invoice ID
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create invoice for partner {partner_id}")
            return {"status": "dry_run", "message": "Invoice not created (dry run mode)"}
        
        try:
            # Create invoice
            invoice_data = {
                'move_type': invoice_type,
                'partner_id': partner_id,
                'invoice_line_ids': [(0, 0, {
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount
                })]
            }
            
            invoice_id = self._execute('account.move', 'create', invoice_data)
            
            self.logger.info(f"Created invoice: {invoice_id}")
            
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "message": f"Invoice created successfully"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def confirm_invoice(self, invoice_id: int) -> dict:
        """
        Confirm/post an invoice.
        
        Args:
            invoice_id: Invoice ID to confirm
            
        Returns:
            dict with status
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would confirm invoice {invoice_id}")
            return {"status": "dry_run", "message": "Invoice not confirmed (dry run mode)"}
        
        try:
            self._execute('account.move', 'action_post', [invoice_id])
            
            self.logger.info(f"Confirmed invoice: {invoice_id}")
            
            return {
                "status": "success",
                "message": f"Invoice {invoice_id} confirmed"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_account_summary(self) -> dict:
        """
        Get accounting summary.
        
        Returns:
            dict with account summary
        """
        try:
            # Get total receivables
            receivables = self._execute(
                'account.move',
                'search_read',
                domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                fields=['amount_total', 'amount_due']
            )
            
            total_receivable = sum(inv['amount_due'] or 0 for inv in receivables)
            
            # Get total payables
            payables = self._execute(
                'account.move',
                'search_read',
                domain=[('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
                fields=['amount_total', 'amount_due']
            )
            
            total_payable = sum(inv['amount_due'] or 0 for inv in payables)
            
            return {
                "status": "success",
                "summary": {
                    "total_receivable": total_receivable,
                    "total_payable": total_payable,
                    "net_position": total_receivable - total_payable,
                    "invoice_count": len(receivables),
                    "bill_count": len(payables)
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== Partners (Customers/Vendors) ====================
    
    def get_partners(self, limit: int = 20, customer: bool = True) -> dict:
        """
        Get list of partners (customers/vendors).
        
        Args:
            limit: Maximum number of partners
            customer: Filter for customers (False for vendors)
            
        Returns:
            dict with list of partners
        """
        try:
            domain = []
            if customer:
                domain.append(('customer_rank', '>', 0))
            
            partners = self._execute(
                'res.partner',
                'search_read',
                domain=domain,
                fields=['name', 'email', 'phone', 'city', 'country_id'],
                limit=limit
            )
            
            return {
                "status": "success",
                "count": len(partners),
                "partners": partners
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_partner(self, name: str, email: str = None, 
                       phone: str = None, is_customer: bool = True) -> dict:
        """
        Create a new partner.
        
        Args:
            name: Partner name
            email: Email address
            phone: Phone number
            is_customer: Is a customer (vs vendor)
            
        Returns:
            dict with partner ID
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create partner: {name}")
            return {"status": "dry_run", "message": "Partner not created (dry run mode)"}
        
        try:
            partner_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'customer_rank': 1 if is_customer else 0,
                'supplier_rank': 0 if is_customer else 1
            }
            
            partner_id = self._execute('res.partner', 'create', partner_data)
            
            self.logger.info(f"Created partner: {name} (ID: {partner_id})")
            
            return {
                "status": "success",
                "partner_id": partner_id,
                "message": f"Partner {name} created successfully"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== Products ====================
    
    def get_products(self, limit: int = 20) -> dict:
        """
        Get list of products.
        
        Args:
            limit: Maximum number of products
            
        Returns:
            dict with list of products
        """
        try:
            products = self._execute(
                'product.template',
                'search_read',
                domain=[],
                fields=['name', 'list_price', 'categ_id', 'type'],
                limit=limit
            )
            
            return {
                "status": "success",
                "count": len(products),
                "products": products
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_product(self, name: str, price: float, 
                       category: str = None) -> dict:
        """
        Create a new product.
        
        Args:
            name: Product name
            price: Sale price
            category: Product category
            
        Returns:
            dict with product ID
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create product: {name}")
            return {"status": "dry_run", "message": "Product not created (dry run mode)"}
        
        try:
            product_data = {
                'name': name,
                'list_price': price,
                'type': 'product'
            }
            
            product_id = self._execute('product.template', 'create', product_data)
            
            self.logger.info(f"Created product: {name} (ID: {product_id})")
            
            return {
                "status": "success",
                "product_id": product_id,
                "message": f"Product {name} created successfully"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== Reports ====================
    
    def get_weekly_revenue(self) -> dict:
        """
        Get weekly revenue summary.
        
        Returns:
            dict with revenue data
        """
        try:
            from datetime import timedelta
            
            # Calculate date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            invoices = self._execute(
                'account.move',
                'search_read',
                domain=[
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', start_date.strftime('%Y-%m-%d')),
                    ('invoice_date', '<=', end_date.strftime('%Y-%m-%d'))
                ],
                fields=['name', 'amount_total', 'invoice_date']
            )
            
            total_revenue = sum(inv['amount_total'] or 0 for inv in invoices)
            
            return {
                "status": "success",
                "period": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "total_revenue": total_revenue,
                "invoice_count": len(invoices),
                "invoices": invoices
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def create_mcp_server():
    """Create and run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP library not available. Running in standalone mode.")
        return None
    
    server = Server("odoo-mcp")
    odoo_service = OdooMCPServer()
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="get_invoices",
                description="Get list of invoices from Odoo",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max invoices"},
                        "state": {"type": "string", "enum": ["draft", "posted", "cancel"]}
                    }
                }
            ),
            Tool(
                name="create_invoice",
                description="Create a new customer invoice",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "partner_id": {"type": "integer", "description": "Customer ID"},
                        "amount": {"type": "number", "description": "Invoice amount"},
                        "description": {"type": "string", "description": "Description"}
                    },
                    "required": ["partner_id", "amount", "description"]
                }
            ),
            Tool(
                name="confirm_invoice",
                description="Confirm/post an invoice",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "invoice_id": {"type": "integer", "description": "Invoice ID"}
                    },
                    "required": ["invoice_id"]
                }
            ),
            Tool(
                name="get_account_summary",
                description="Get accounting summary (receivables, payables)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_partners",
                description="Get list of partners (customers/vendors)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"},
                        "customer": {"type": "boolean"}
                    }
                }
            ),
            Tool(
                name="create_partner",
                description="Create a new partner (customer/vendor)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "is_customer": {"type": "boolean"}
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="get_weekly_revenue",
                description="Get weekly revenue summary",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "get_invoices":
            result = odoo_service.get_invoices(
                limit=arguments.get("limit", 10),
                state=arguments.get("state")
            )
        elif name == "create_invoice":
            result = odoo_service.create_invoice(
                partner_id=arguments.get("partner_id"),
                amount=arguments.get("amount"),
                description=arguments.get("description")
            )
        elif name == "confirm_invoice":
            result = odoo_service.confirm_invoice(
                invoice_id=arguments.get("invoice_id")
            )
        elif name == "get_account_summary":
            result = odoo_service.get_account_summary()
        elif name == "get_partners":
            result = odoo_service.get_partners(
                limit=arguments.get("limit", 20),
                customer=arguments.get("customer", True)
            )
        elif name == "create_partner":
            result = odoo_service.create_partner(
                name=arguments.get("name"),
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                is_customer=arguments.get("is_customer", True)
            )
        elif name == "get_weekly_revenue":
            result = odoo_service.get_weekly_revenue()
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return server


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Odoo MCP Server')
    parser.add_argument('--url', help='Odoo server URL')
    parser.add_argument('--db', help='Database name')
    parser.add_argument('--username', help='Admin username')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    
    if not ODOO_AVAILABLE:
        print("Odoo dependencies not available. Install with: pip install xmlrpc3 requests")
        print("Odoo MCP Server ready (standalone mode - no connection)")
        return
    
    if not MCP_AVAILABLE:
        print("MCP not available. Run in standalone mode for testing.")
        odoo_service = OdooMCPServer(
            url=args.url, db=args.db, 
            username=args.username, password=args.password
        )
        print(f"Connected to Odoo: {odoo_service.uid is not None}")
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
