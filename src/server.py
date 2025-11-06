#!/usr/bin/env python3
"""
Indico MCP Server - Main Entry Point
====================================
Provides MCP interface to CERN Indico events system.

Usage:
    python server.py

Environment Variables:
    LOG_LEVEL - Logging level (DEBUG, INFO, WARNING, ERROR)
    CACHE_SIZE - LRU cache size for API responses
    ENABLE_CACHE - Enable/disable caching (true/false)

Note: This server only accesses PUBLIC events for security purposes.
"""

import logging
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

from src.config import Config
from src.client import IndicoClient
from src.models import EventNormalizer
from src.utils import (
    DateRange, 
    validate_limit, 
    validate_event_id, 
    validate_category_id,
    sanitize_keyword,
    calculate_fetch_limit
)

# Setup
logger = logging.getLogger(__name__)
app = FastMCP("indico")

# Initialize components
client = IndicoClient()
normalizer = EventNormalizer()


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
    Uses intelligent filtering to find relevant events efficiently.
    
    Args:
        keyword: Text to search for in event titles (case-insensitive)
        limit: Maximum number of results (1-500, default 10)
        category_id: Indico category ID (0 for all categories, default 0)
        days_ahead: Days to look ahead (overrides default 30)
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (overrides days_ahead)
        
    Returns:
        List of events matching the search criteria
        
    Raises:
        ValueError: If parameters are invalid or API call fails
        
    Examples:
        search_events("machine learning", limit=5)
        search_events("physics", days_ahead=14, category_id=123)
        search_events("seminar", from_date="2025-01-01", to_date="2025-01-31")
    """
    try:
        # Validate and sanitize inputs
        keyword = sanitize_keyword(keyword)
        limit = validate_limit(limit)
        category_id = validate_category_id(category_id)
        
        # Calculate date range
        date_range = DateRange(default_days=30)
        start, end = date_range.calculate(from_date, to_date, days_ahead)
        
        # Calculate fetch limit for filtering
        fetch_limit = calculate_fetch_limit(limit)
        
        # Fetch events from API
        events = client.fetch_events(category_id, start, end, fetch_limit)
        
        # Filter by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        filtered = [
            event for event in events 
            if keyword_lower in event.get("title", "").lower()
        ]
        
        # Limit and normalize results
        limited_events = filtered[:limit]
        results = normalizer.normalize_list(limited_events)
        
        logger.info(f"Search '{keyword}' found {len(results)} matches out of {len(events)} events")
        return results
        
    except Exception as e:
        logger.error(f"Search failed for keyword '{keyword}': {e}")
        raise


@app.tool()
def get_event_details(event_id: int) -> Dict[str, Any]:
    """
    Get detailed information for a specific public Indico event.
    
    Retrieves comprehensive event information including description,
    organizers, and other metadata.
    
    Args:
        event_id: Numeric Indico event ID (must be positive)
        
    Returns:
        Detailed event information with description field
        
    Raises:
        ValueError: If event_id is invalid or event not found
        
    Examples:
        get_event_details(1234567)
    """
    try:
        # Validate input
        event_id = validate_event_id(event_id)
        
        # Fetch event details
        event_data = client.fetch_event_details(event_id)
        
        if not event_data:
            return {"error": f"No public event found with ID {event_id}"}
        
        # Normalize with description
        event = normalizer.normalize(event_data, include_description=True)
        
        if not event:
            return {"error": f"Failed to process event data for ID {event_id}"}
        
        result = event.to_dict()
        logger.info(f"Retrieved details for event {event_id}: '{event.title}'")
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
    
    Retrieves events scheduled in the near future, useful for
    discovering what's happening at CERN.
    
    Args:
        days: Days to look ahead (default 7)
        limit: Maximum events to return (1-500, default 10)
        category_id: Indico category ID (0 for all, default 0)
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (overrides days)
        
    Returns:
        List of upcoming events sorted by start date
        
    Raises:
        ValueError: If parameters are invalid or API call fails
        
    Examples:
        upcoming_public()  # Next 7 days
        upcoming_public(days=14, limit=20)  # Next 2 weeks, 20 events
        upcoming_public(from_date="2025-01-01", to_date="2025-01-07")
    """
    try:
        # Validate inputs
        limit = validate_limit(limit)
        category_id = validate_category_id(category_id)
        
        # Calculate date range
        date_range = DateRange(default_days=7)
        start, end = date_range.calculate(from_date, to_date, days)
        
        # Fetch events
        events = client.fetch_events(category_id, start, end, limit)
        
        # Normalize results
        results = normalizer.normalize_list(events)
        
        logger.info(f"Listed {len(results)} upcoming events from {start} to {end}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to list upcoming events: {e}")
        raise


@app.tool()
def server_status() -> Dict[str, Any]:
    """
    Get server status and configuration information.
    
    Returns:
        Server status including authentication, cache stats, and configuration
    """
    try:
        status = {
            "version": "2.0.0",
            "public_only": True,
            "base_url": Config.INDICO_BASE_URL,
            "cache_enabled": Config.ENABLE_CACHE,
            "max_limit": Config.MAX_LIMIT,
            "default_limit": Config.DEFAULT_LIMIT
        }
        
        # Add cache statistics if available
        cache_info = client.get_cache_info()
        if cache_info:
            status["cache_stats"] = cache_info
            
        logger.info("Server status requested")
        return status
        
    except Exception as e:
        logger.error(f"Failed to get server status: {e}")
        return {"error": "Failed to retrieve server status"}


def main():
    """Initialize and run the MCP server."""
    try:
        # Print startup banner
        print("=" * 60)
        print("Indico MCP Server v2.0.0")
        print(f"Base URL: {Config.INDICO_BASE_URL}")
        print("Access: PUBLIC EVENTS ONLY")
        print(f"Cache: {'ENABLED' if Config.ENABLE_CACHE else 'DISABLED'}")
        print(f"Log Level: {Config.LOG_LEVEL}")
        print("=" * 60)

        logger.info("Starting Indico MCP Server v2.0.0 (PUBLIC ACCESS ONLY)")
        logger.info(f"Configuration: Cache={Config.ENABLE_CACHE}")
        
        # Start the server
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped gracefully")
        
    except Exception as e:
        logger.critical(f"Server failed to start: {e}")
        print(f"\nERROR: Server failed to start: {e}")
        raise


if __name__ == "__main__":
    main()