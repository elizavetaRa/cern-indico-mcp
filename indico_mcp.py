#!/usr/bin/env python3
"""
Indico MCP Server - Production Ready
====================================
Provides secure, cached access to CERN Indico public events via MCP protocol.

Author: [Your Name]
Version: 2.0.0
License: MIT
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management."""
    
    INDICO_BASE_URL = os.getenv("INDICO_BASE_URL", "https://indico.cern.ch")
    INDICO_EXPORT = f"{INDICO_BASE_URL}/export"
    INDICO_TOKEN = os.getenv("INDICO_TOKEN", "").strip()
    
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 500
    DEFAULT_DAYS_AHEAD = 30
    DEFAULT_UPCOMING_DAYS = 7
    
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    CACHE_SIZE = 128
    
    # API limits
    FETCH_MULTIPLIER = 10  # Fetch 10x requested for filtering
    MIN_FETCH_LIMIT = 100


class DateRange:
    """Date range handler with validation."""
    
    def __init__(self, default_days: int = Config.DEFAULT_DAYS_AHEAD):
        self.default_days = default_days
    
    def calculate(
        self, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Calculate and validate date range.
        
        Returns:
            Tuple of (start_date, end_date) in ISO format
            
        Raises:
            ValueError: If dates are invalid or range is invalid
        """
        # Start date
        if from_date:
            try:
                start = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid from_date format: {from_date}. Use YYYY-MM-DD")
        else:
            start = datetime.now().date()
        
        # End date
        if to_date:
            try:
                end = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid to_date format: {to_date}. Use YYYY-MM-DD")
        elif days is not None:
            if days < 0:
                raise ValueError(f"days must be positive, got {days}")
            end = start + timedelta(days=days)
        else:
            end = start + timedelta(days=self.default_days)
        
        # Validate range
        if end < start:
            raise ValueError(f"End date {end} is before start date {start}")
        
        if (end - start).days > 365:
            raise ValueError("Date range cannot exceed 365 days")
        
        return start.isoformat(), end.isoformat()


class IndicoClient:
    """Handles all Indico API interactions with retry logic and caching."""
    
    def __init__(self):
        self.session = self._create_session()
        self.headers = self._setup_headers()
        
    def _create_session(self) -> requests.Session:
        """Create session with retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=Config.MAX_RETRIES,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _setup_headers(self) -> Dict[str, str]:
        """Setup authorization headers if token is available."""
        headers = {"User-Agent": "Indico-MCP/2.0"}
        
        if Config.INDICO_TOKEN and Config.INDICO_TOKEN != 'your_token_here':
            headers["Authorization"] = f"Bearer {Config.INDICO_TOKEN}"
            logger.info("Running with authentication token")
        else:
            logger.info("Running without authentication - public events only")
            
        return headers
    
    @lru_cache(maxsize=Config.CACHE_SIZE)
    def fetch_events(
        self,
        category_id: int,
        start_date: str,
        end_date: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from Indico API with caching.
        
        Cached based on parameters to avoid repeated API calls.
        """
        url = f"{Config.INDICO_EXPORT}/categ/{category_id}.json"
        params = {
            "limit": limit,
            "order": "start",
            "onlypublic": "yes",
            "from": start_date,
            "to": end_date
        }
        
        try:
            logger.debug(f"Fetching events: {params}")
            response = self.session.get(
                url, 
                params=params, 
                headers=self.headers, 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            events = data.get("results", [])
            logger.info(f"Fetched {len(events)} events from Indico")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch events: {e}")
            raise ValueError(f"Failed to fetch events from Indico: {str(e)}")
    
    def fetch_event_details(self, event_id: int) -> Dict[str, Any]:
        """Fetch detailed information for a single event."""
        url = f"{Config.INDICO_EXPORT}/event/{event_id}.json"
        params = {"onlypublic": "yes", "detail": "events"}
        
        try:
            logger.debug(f"Fetching event details for ID: {event_id}")
            response = self.session.get(
                url,
                params=params,
                headers=self.headers,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"No event found with ID: {event_id}")
                return None
                
            return results[0]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch event {event_id}: {e}")
            raise ValueError(f"Failed to fetch event details: {str(e)}")


class EventNormalizer:
    """Handles event data transformation and normalization."""
    
    @staticmethod
    def normalize(event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw Indico event to normalized format."""
        if not event:
            return None
            
        start_date = event.get("startDate", {})
        end_date = event.get("endDate", {})
        
        return {
            "id": event.get("id"),
            "title": event.get("title", ""),
            "category": event.get("category", event.get("categoryTitle", "")),
            "start": EventNormalizer._format_datetime(start_date),
            "end": EventNormalizer._format_datetime(end_date),
            "location": event.get("roomFullname") or event.get("location") or "N/A",
            "type": event.get("type", ""),
            "url": event.get("url", ""),
        }
    
    @staticmethod
    def _format_datetime(dt_dict: Dict[str, str]) -> Optional[str]:
        """Format datetime dictionary to readable string."""
        if not dt_dict:
            return None
            
        date = dt_dict.get("date")
        time = dt_dict.get("time", "")
        tz = dt_dict.get("tz", "Europe/Zurich")
        
        if not date:
            return None
            
        if time:
            return f"{date} {time} ({tz})"
        return f"{date} ({tz})"


# ──────────────────────────────────────────────────────────────
# MCP Server Implementation
# ──────────────────────────────────────────────────────────────

app = FastMCP("indico")
client = IndicoClient()
normalizer = EventNormalizer()


def validate_limit(limit: int) -> int:
    """Validate and constrain limit parameter."""
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if limit > Config.MAX_LIMIT:
        logger.warning(f"Limit {limit} exceeds maximum, using {Config.MAX_LIMIT}")
        return Config.MAX_LIMIT
    return limit


@app.tool()
def search_events(
    keyword: str,
    limit: int = Config.DEFAULT_LIMIT,
    category_id: int = 0,
    days_ahead: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search upcoming public CERN Indico events by keyword.
    
    Searches event titles for the specified keyword within the given date range.
    
    Args:
        keyword: Text to search for in event titles (case-insensitive)
        limit: Maximum number of results to return (1-500, default 10)
        category_id: Indico category ID (0 for all categories)
        days_ahead: Days to look ahead (overrides default 30)
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (overrides days_ahead)
        
    Returns:
        List of normalized event dictionaries matching the search
        
    Raises:
        ValueError: If parameters are invalid or API call fails
    """
    try:
        # Validate inputs
        limit = validate_limit(limit)
        if not keyword.strip():
            raise ValueError("Keyword cannot be empty")
        
        # Calculate date range
        date_range = DateRange(default_days=30)
        start, end = date_range.calculate(from_date, to_date, days_ahead)
        
        # Fetch more results for client-side filtering
        fetch_limit = min(
            max(limit * Config.FETCH_MULTIPLIER, Config.MIN_FETCH_LIMIT),
            Config.MAX_LIMIT
        )
        
        # Get events
        events = client.fetch_events(category_id, start, end, fetch_limit)
        
        # Filter by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        filtered = [
            e for e in events 
            if keyword_lower in e.get("title", "").lower()
        ]
        
        # Normalize and limit results
        results = [normalizer.normalize(e) for e in filtered[:limit]]
        
        logger.info(f"Search '{keyword}' found {len(results)} matches")
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise


@app.tool()
def get_event_details(event_id: int) -> Dict[str, Any]:
    """
    Get detailed information for a specific public Indico event.
    
    Args:
        event_id: Numeric Indico event ID
        
    Returns:
        Normalized event dictionary with description field
        
    Raises:
        ValueError: If event_id is invalid or event not found
    """
    try:
        if event_id < 1:
            raise ValueError("Event ID must be positive")
            
        event = client.fetch_event_details(event_id)
        
        if not event:
            return {"error": f"No public event found with ID {event_id}"}
        
        # Normalize and add description
        result = normalizer.normalize(event)
        result["description"] = event.get("description", "")
        
        logger.info(f"Retrieved details for event {event_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {e}")
        raise


@app.tool()
def upcoming_public(
    days: Optional[int] = None,
    limit: int = Config.DEFAULT_LIMIT,
    category_id: int = 0,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List upcoming public events at CERN.
    
    Args:
        days: Days to look ahead (default 7)
        limit: Maximum events to return (1-500, default 10)
        category_id: Indico category ID (0 for all)
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (overrides days)
        
    Returns:
        List of normalized upcoming events
        
    Raises:
        ValueError: If parameters are invalid or API call fails
    """
    try:
        # Validate limit
        limit = validate_limit(limit)
        
        # Calculate date range
        date_range = DateRange(default_days=7)
        start, end = date_range.calculate(from_date, to_date, days)
        
        # Fetch events
        events = client.fetch_events(category_id, start, end, limit)
        
        # Normalize results
        results = [normalizer.normalize(e) for e in events]
        
        logger.info(f"Listed {len(results)} upcoming events")
        return results
        
    except Exception as e:
        logger.error(f"Failed to list upcoming events: {e}")
        raise


# ──────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────

def main():
    """Initialize and run the MCP server."""
    try:
        if not Config.INDICO_TOKEN or Config.INDICO_TOKEN == 'your_token_here':
            print("=" * 60)
            print("Running in PUBLIC MODE - No authentication token")
            print("To access restricted events, add token to .env file")
            print("Get token from: https://indico.cern.ch/user/tokens/")
            print("=" * 60)
        else:
            print("Running with authentication token")
            
        logger.info("Starting Indico MCP Server v2.0")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}")
        raise


if __name__ == "__main__":
    main()