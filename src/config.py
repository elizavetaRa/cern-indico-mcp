"""
Configuration module for Indico MCP Server.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration management."""
    
    # API Configuration (PUBLIC ACCESS ONLY)
    INDICO_BASE_URL = os.getenv("INDICO_BASE_URL", "https://indico.cern.ch")
    INDICO_EXPORT = f"{INDICO_BASE_URL}/export"
    
    # Default Values
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 500
    DEFAULT_DAYS_AHEAD = 30
    DEFAULT_UPCOMING_DAYS = 7
    
    # Network Configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "0.3"))
    
    # Performance Configuration
    CACHE_SIZE = int(os.getenv("CACHE_SIZE", "128"))
    FETCH_MULTIPLIER = 10  # Fetch 10x requested for filtering
    MIN_FETCH_LIMIT = 100
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Feature Flags
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if running with valid authentication (always False for security)."""
        return False
    
    @classmethod
    def get_user_agent(cls) -> str:
        """Generate user agent string."""
        from src import __version__
        return f"Indico-MCP/{__version__}"


# Setup logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format=Config.LOG_FORMAT
)

logger = logging.getLogger(__name__)