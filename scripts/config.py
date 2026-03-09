"""
Configuration Module

Loads and validates environment variables from .env file.
Provides a central configuration object for the entire application.

Usage:
    from config import Config
    config = Config()
    
    # Access configuration
    odoo_url = config.ODOO_URL
    facebook_token = config.FACEBOOK_ACCESS_TOKEN
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """
    Central configuration for AI Employee.
    
    Loads environment variables from:
    1. System environment variables
    2. .env file in project root
    """
    
    def __init__(self, env_path: str = None):
        """
        Initialize configuration.
        
        Args:
            env_path: Path to .env file (default: project root/.env)
        """
        # Find project root
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # Load .env file
        if env_path:
            env_file = Path(env_path)
        else:
            env_file = self.PROJECT_ROOT / '.env'
        
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        
        # =====================================================================
        # Application Settings
        # =====================================================================
        self.VAULT_PATH = self._get_env(
            'VAULT_PATH',
            default=str(self.PROJECT_ROOT / 'AI_Employee_Vault')
        )
        self.DRY_RUN = self._get_env_bool('DRY_RUN', default=False)
        self.LOG_LEVEL = self._get_env('LOG_LEVEL', default='INFO')
        
        # =====================================================================
        # Odoo ERP Configuration
        # =====================================================================
        self.ODOO_URL = self._get_env('ODOO_URL', default='http://localhost:8069')
        self.ODOO_DB = self._get_env('ODOO_DB', default='odoo')
        self.ODOO_USERNAME = self._get_env('ODOO_USERNAME', default='admin')
        self.ODOO_PASSWORD = self._get_env('ODOO_PASSWORD', default='admin')
        self.ODOO_MASTER_PASSWORD = self._get_env(
            'ODOO_MASTER_PASSWORD',
            default='admin'
        )
        
        # =====================================================================
        # Facebook Graph API Configuration
        # =====================================================================
        self.FACEBOOK_APP_ID = self._get_env('FACEBOOK_APP_ID', default='')
        self.FACEBOOK_APP_SECRET = self._get_env('FACEBOOK_APP_SECRET', default='')
        self.FACEBOOK_ACCESS_TOKEN = self._get_env('FACEBOOK_ACCESS_TOKEN', default='')
        self.FACEBOOK_PAGE_ID = self._get_env('FACEBOOK_PAGE_ID', default='')
        self.FACEBOOK_API_VERSION = self._get_env('FACEBOOK_API_VERSION', default='v19.0')
        
        # =====================================================================
        # LinkedIn API Configuration
        # =====================================================================
        self.LINKEDIN_CLIENT_ID = self._get_env('LINKEDIN_CLIENT_ID', default='')
        self.LINKEDIN_CLIENT_SECRET = self._get_env('LINKEDIN_CLIENT_SECRET', default='')
        self.LINKEDIN_ACCESS_TOKEN = self._get_env('LINKEDIN_ACCESS_TOKEN', default='')
        self.LINKEDIN_ORGANIZATION_ID = self._get_env('LINKEDIN_ORGANIZATION_ID', default='')
        
        # =====================================================================
        # Gmail API Configuration
        # =====================================================================
        self.GMAIL_CLIENT_ID = self._get_env('GMAIL_CLIENT_ID', default='')
        self.GMAIL_CLIENT_SECRET = self._get_env('GMAIL_CLIENT_SECRET', default='')
        self.GMAIL_CREDENTIALS_PATH = self._get_env(
            'GMAIL_CREDENTIALS_PATH',
            default=str(self.PROJECT_ROOT / 'credentials.json')
        )
        self.GMAIL_TOKEN_PATH = self._get_env(
            'GMAIL_TOKEN_PATH',
            default=str(Path.home() / '.gmail' / 'token.json')
        )
        self.GMAIL_API_KEY = self._get_env('GMAIL_API_KEY', default='')
        
        # =====================================================================
        # Session Paths
        # =====================================================================
        self.LINKEDIN_SESSION_PATH = self._get_env(
            'LINKEDIN_SESSION_PATH',
            default=str(Path.home() / '.linkedin_session')
        )
        self.FACEBOOK_SESSION_PATH = self._get_env(
            'FACEBOOK_SESSION_PATH',
            default=str(Path.home() / '.facebook_session')
        )
        self.WHATSAPP_SESSION_PATH = self._get_env(
            'WHATSAPP_SESSION_PATH',
            default=str(Path.home() / '.whatsapp_session')
        )
        
        # =====================================================================
        # Watcher Configuration
        # =====================================================================
        self.GMAIL_CHECK_INTERVAL = self._get_env_int('GMAIL_CHECK_INTERVAL', default=120)
        self.LINKEDIN_CHECK_INTERVAL = self._get_env_int('LINKEDIN_CHECK_INTERVAL', default=300)
        self.FACEBOOK_CHECK_INTERVAL = self._get_env_int('FACEBOOK_CHECK_INTERVAL', default=300)
        self.FILESYSTEM_CHECK_INTERVAL = self._get_env_int('FILESYSTEM_CHECK_INTERVAL', default=30)
        
        # =====================================================================
        # Approval Workflow Configuration
        # =====================================================================
        self.AUTO_APPROVE_EMAIL_RECIPIENTS_THRESHOLD = self._get_env_int(
            'AUTO_APPROVE_EMAIL_RECIPIENTS_THRESHOLD',
            default=5
        )
        self.AUTO_APPROVE_PAYMENT_THRESHOLD = self._get_env_float(
            'AUTO_APPROVE_PAYMENT_THRESHOLD',
            default=0
        )
        self.APPROVAL_EXPIRATION_HOURS = self._get_env_int(
            'APPROVAL_EXPIRATION_HOURS',
            default=24
        )
        
        # =====================================================================
        # Audit Logging Configuration
        # =====================================================================
        self.AUDIT_LOG_RETENTION_DAYS = self._get_env_int(
            'AUDIT_LOG_RETENTION_DAYS',
            default=90
        )
        self.AUDIT_LOGGING_ENABLED = self._get_env_bool(
            'AUDIT_LOGGING_ENABLED',
            default=True
        )
        
        # =====================================================================
        # Ralph Wiggum Loop Configuration
        # =====================================================================
        self.RALPH_MAX_ITERATIONS = self._get_env_int('RALPH_MAX_ITERATIONS', default=10)
        self.RALPH_ITERATION_TIMEOUT = self._get_env_int(
            'RALPH_ITERATION_TIMEOUT',
            default=300
        )
        
        # =====================================================================
        # Scheduler Configuration
        # =====================================================================
        self.DAILY_BRIEFING_TIME = self._get_env('DAILY_BRIEFING_TIME', default='08:00')
        self.WEEKLY_AUDIT_DAY = self._get_env_int('WEEKLY_AUDIT_DAY', default=0)
        self.WEEKLY_AUDIT_TIME = self._get_env('WEEKLY_AUDIT_TIME', default='22:00')
        
        # =====================================================================
        # Docker Configuration
        # =====================================================================
        self.DOCKER_NETWORK_NAME = self._get_env('DOCKER_NETWORK_NAME', default='odoo_network')
        self.ODOO_CONTAINER_NAME = self._get_env('ODOO_CONTAINER_NAME', default='ai_employee_odoo')
        self.POSTGRES_CONTAINER_NAME = self._get_env(
            'POSTGRES_CONTAINER_NAME',
            default='ai_employee_odoo_db'
        )
        self.POSTGRES_DB = self._get_env('POSTGRES_DB', default='odoo')
        self.POSTGRES_USER = self._get_env('POSTGRES_USER', default='odoo')
        self.POSTGRES_PASSWORD = self._get_env('POSTGRES_PASSWORD', default='odoo_password')
        self.ODOO_PORT = self._get_env_int('ODOO_PORT', default=8069)
        
        # =====================================================================
        # Security Configuration
        # =====================================================================
        self.ENCRYPTION_KEY = self._get_env('ENCRYPTION_KEY', default='')
        self.SESSION_SECRET = self._get_env('SESSION_SECRET', default='')
        
        # =====================================================================
        # Optional: Cloud/Remote Configuration
        # =====================================================================
        self.CLOUD_VM_URL = self._get_env('CLOUD_VM_URL', default='')
        self.CLOUD_API_KEY = self._get_env('CLOUD_API_KEY', default='')
        self.VAULT_SYNC_METHOD = self._get_env('VAULT_SYNC_METHOD', default='git')
        self.VAULT_GIT_REMOTE = self._get_env('VAULT_GIT_REMOTE', default='')
        
        # =====================================================================
        # Optional: Additional Integrations
        # =====================================================================
        self.TWITTER_API_KEY = self._get_env('TWITTER_API_KEY', default='')
        self.TWITTER_API_SECRET = self._get_env('TWITTER_API_SECRET', default='')
        self.TWITTER_ACCESS_TOKEN = self._get_env('TWITTER_ACCESS_TOKEN', default='')
        self.INSTAGRAM_ACCESS_TOKEN = self._get_env('INSTAGRAM_ACCESS_TOKEN', default='')
        self.INSTAGRAM_BUSINESS_ACCOUNT_ID = self._get_env(
            'INSTAGRAM_BUSINESS_ACCOUNT_ID',
            default=''
        )
        self.WHATSAPP_BUSINESS_PHONE_ID = self._get_env(
            'WHATSAPP_BUSINESS_PHONE_ID',
            default=''
        )
        self.WHATSAPP_BUSINESS_TOKEN = self._get_env('WHATSAPP_BUSINESS_TOKEN', default='')
    
    def _get_env(self, key: str, default: str = '') -> str:
        """Get environment variable as string."""
        return os.getenv(key, default)
    
    def _get_env_int(self, key: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def _get_env_float(self, key: str, default: float = 0.0) -> float:
        """Get environment variable as float."""
        try:
            return float(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def validate(self) -> tuple:
        """
        Validate required configuration.
        
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []
        
        # Check vault path exists
        vault_path = Path(self.VAULT_PATH)
        if not vault_path.exists():
            errors.append(f"Vault path does not exist: {self.VAULT_PATH}")
        
        # Check Odoo configuration
        if not self.ODOO_URL:
            errors.append("ODOO_URL is required")
        
        # Check Gmail credentials path exists
        gmail_creds = Path(self.GMAIL_CREDENTIALS_PATH)
        if not gmail_creds.exists():
            errors.append(f"Gmail credentials not found: {self.GMAIL_CREDENTIALS_PATH}")
        
        # Warn about empty API keys (not errors, just warnings)
        warnings = []
        if not self.FACEBOOK_ACCESS_TOKEN:
            warnings.append("FACEBOOK_ACCESS_TOKEN not set - Facebook features disabled")
        if not self.LINKEDIN_ACCESS_TOKEN:
            warnings.append("LINKEDIN_ACCESS_TOKEN not set - LinkedIn API features disabled")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors, warnings
    
    def __str__(self) -> str:
        """String representation (without sensitive data)."""
        return f"""
Configuration:
  Vault Path: {self.VAULT_PATH}
  Odoo URL: {self.ODOO_URL}
  Dry Run: {self.DRY_RUN}
  Log Level: {self.LOG_LEVEL}
  Gmail Check Interval: {self.GMAIL_CHECK_INTERVAL}s
  LinkedIn Check Interval: {self.LINKEDIN_CHECK_INTERVAL}s
  Facebook Check Interval: {self.FACEBOOK_CHECK_INTERVAL}s
"""


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from .env file."""
    global _config
    _config = Config()
    return _config
