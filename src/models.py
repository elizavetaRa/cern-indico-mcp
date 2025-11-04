"""
Data models and normalization for Indico events.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """Normalized event data model."""
    id: str
    title: str
    category: str
    start: Optional[str]
    end: Optional[str]
    location: str
    type: str
    url: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "type": self.type,
            "url": self.url
        }
        if self.description is not None:
            result["description"] = self.description
        return result


class EventNormalizer:
    """Handles event data transformation and normalization."""
    
    @staticmethod
    def normalize(event_data: Dict[str, Any], include_description: bool = False) -> Optional[Event]:
        """
        Convert raw Indico event to normalized Event model.
        
        Args:
            event_data: Raw event dictionary from Indico API
            include_description: Whether to include description field
            
        Returns:
            Normalized Event object or None if invalid
        """
        if not event_data:
            return None
        
        try:
            # Extract dates
            start_date = event_data.get("startDate", {})
            end_date = event_data.get("endDate", {})
            
            # Create Event object
            event = Event(
                id=str(event_data.get("id", "")),
                title=event_data.get("title", ""),
                category=event_data.get("category", event_data.get("categoryTitle", "")),
                start=EventNormalizer._format_datetime(start_date),
                end=EventNormalizer._format_datetime(end_date),
                location=event_data.get("roomFullname") or event_data.get("location") or "N/A",
                type=event_data.get("type", ""),
                url=event_data.get("url", "")
            )
            
            if include_description:
                event.description = event_data.get("description", "")
            
            return event
            
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to normalize event: {e}")
            return None
    
    @staticmethod
    def _format_datetime(dt_dict: Dict[str, str]) -> Optional[str]:
        """
        Format datetime dictionary to readable string.
        
        Args:
            dt_dict: Dictionary with date, time, and timezone
            
        Returns:
            Formatted datetime string or None
        """
        if not dt_dict or not isinstance(dt_dict, dict):
            return None
            
        date = dt_dict.get("date")
        if not date:
            return None
            
        time = dt_dict.get("time", "")
        tz = dt_dict.get("tz", "Europe/Zurich")
        
        # Format based on available information
        if time:
            return f"{date} {time} ({tz})"
        return f"{date} ({tz})"
    
    @staticmethod
    def normalize_list(events: list, include_description: bool = False) -> list:
        """
        Normalize a list of events.
        
        Args:
            events: List of raw event dictionaries
            include_description: Whether to include descriptions
            
        Returns:
            List of Event dictionaries
        """
        normalized = []
        for event_data in events:
            event = EventNormalizer.normalize(event_data, include_description)
            if event:
                normalized.append(event.to_dict())
        return normalized


# Import logger after defining classes to avoid circular import
import logging
logger = logging.getLogger(__name__)