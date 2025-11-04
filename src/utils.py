"""
Utility functions for Indico MCP Server.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .config import Config

logger = logging.getLogger(__name__)


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
        
        Args:
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format  
            days: Number of days from start date
            
        Returns:
            Tuple of (start_date, end_date) in ISO format
            
        Raises:
            ValueError: If dates are invalid or range is invalid
        """
        # Parse start date
        if from_date:
            try:
                start = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid from_date format: {from_date}. Use YYYY-MM-DD")
        else:
            start = datetime.now().date()
        
        # Parse end date
        if to_date:
            try:
                end = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid to_date format: {to_date}. Use YYYY-MM-DD")
        elif days is not None:
            if days < 0:
                raise ValueError(f"days must be positive, got {days}")
            if days > 365:
                raise ValueError(f"days cannot exceed 365, got {days}")
            end = start + timedelta(days=days)
        else:
            end = start + timedelta(days=self.default_days)
        
        # Validate range
        if end < start:
            raise ValueError(f"End date {end} is before start date {start}")
        
        days_diff = (end - start).days
        if days_diff > 365:
            raise ValueError(f"Date range cannot exceed 365 days, got {days_diff} days")
        
        logger.debug(f"Date range calculated: {start} to {end}")
        return start.isoformat(), end.isoformat()


def validate_limit(limit: int) -> int:
    """
    Validate and constrain limit parameter.
    
    Args:
        limit: Requested limit value
        
    Returns:
        Valid limit value within constraints
        
    Raises:
        ValueError: If limit is invalid
    """
    if not isinstance(limit, int):
        raise ValueError(f"Limit must be an integer, got {type(limit).__name__}")
        
    if limit < 1:
        raise ValueError(f"Limit must be at least 1, got {limit}")
        
    if limit > Config.MAX_LIMIT:
        logger.warning(f"Limit {limit} exceeds maximum {Config.MAX_LIMIT}, using maximum")
        return Config.MAX_LIMIT
        
    return limit


def validate_category_id(category_id: int) -> int:
    """
    Validate category ID parameter.
    
    Args:
        category_id: Category ID to validate
        
    Returns:
        Valid category ID
        
    Raises:
        ValueError: If category ID is invalid
    """
    if not isinstance(category_id, int):
        raise ValueError(f"Category ID must be an integer, got {type(category_id).__name__}")
        
    if category_id < 0:
        raise ValueError(f"Category ID must be non-negative, got {category_id}")
        
    return category_id


def validate_event_id(event_id: int) -> int:
    """
    Validate event ID parameter.
    
    Args:
        event_id: Event ID to validate
        
    Returns:
        Valid event ID
        
    Raises:
        ValueError: If event ID is invalid
    """
    if not isinstance(event_id, int):
        raise ValueError(f"Event ID must be an integer, got {type(event_id).__name__}")
        
    if event_id < 1:
        raise ValueError(f"Event ID must be positive, got {event_id}")
        
    return event_id


def sanitize_keyword(keyword: str) -> str:
    """
    Sanitize and validate search keyword.
    
    Args:
        keyword: Search keyword to sanitize
        
    Returns:
        Sanitized keyword
        
    Raises:
        ValueError: If keyword is invalid
    """
    if not keyword or not isinstance(keyword, str):
        raise ValueError("Keyword must be a non-empty string")
        
    keyword = keyword.strip()
    
    if not keyword:
        raise ValueError("Keyword cannot be empty or whitespace")
        
    if len(keyword) > 200:
        raise ValueError(f"Keyword too long (max 200 chars), got {len(keyword)}")
        
    return keyword


def calculate_fetch_limit(requested_limit: int) -> int:
    """
    Calculate optimal fetch limit for search operations.
    
    When searching, we need to fetch more results than requested
    to account for client-side filtering.
    
    Args:
        requested_limit: Number of results requested by user
        
    Returns:
        Optimal number of results to fetch from API
    """
    fetch_limit = max(
        requested_limit * Config.FETCH_MULTIPLIER,
        Config.MIN_FETCH_LIMIT
    )
    return min(fetch_limit, Config.MAX_LIMIT)