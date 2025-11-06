"""
Indico API client with retry logic and caching.
"""

import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config

logger = logging.getLogger(__name__)


class IndicoClient:
    """Handles all Indico API interactions with retry logic and caching."""
    
    def __init__(self):
        self.session = self._create_session()
        self.headers = self._setup_headers()
        self._cache_enabled = Config.ENABLE_CACHE
        
    def _create_session(self) -> requests.Session:
        """Create session with retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=Config.MAX_RETRIES,
            backoff_factor=Config.RETRY_BACKOFF,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _setup_headers(self) -> Dict[str, str]:
        """Setup request headers for public-only access."""
        headers = {"User-Agent": Config.get_user_agent()}
        logger.info("Client initialized for public events only (authentication disabled)")
        return headers
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        try:
            logger.debug(f"API request: {url} with params: {params}")
            response = self.session.get(
                url, 
                params=params, 
                headers=self.headers, 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise ValueError("Request timed out. Please try again.")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            raise ValueError("Connection failed. Check your network.")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error("Resource not found")
                raise ValueError("Resource not found.")
            elif e.response.status_code == 403:
                logger.error("Access forbidden - resource may not be public")
                raise ValueError("Access forbidden. This resource may not be public.")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                raise ValueError(f"Server error: {e.response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ValueError(f"Failed to fetch data: {str(e)}")
    
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
        
        Args:
            category_id: Category ID (0 for all)
            start_date: ISO format start date
            end_date: ISO format end date
            limit: Maximum number of events
            
        Returns:
            List of event dictionaries
        """
        url = f"{Config.INDICO_EXPORT}/categ/{category_id}.json"
        params = {
            "limit": limit,
            "order": "start",
            "onlypublic": "yes",
            "from": start_date,
            "to": end_date
        }
        
        data = self._make_request(url, params)
        events = data.get("results", [])
        
        logger.info(f"Fetched {len(events)} events for range {start_date} to {end_date}")
        return events
    
    def fetch_event_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a single event.
        
        Args:
            event_id: Numeric event ID
            
        Returns:
            Event dictionary or None if not found
        """
        url = f"{Config.INDICO_EXPORT}/event/{event_id}.json"
        params = {"onlypublic": "yes", "detail": "events"}
        
        data = self._make_request(url, params)
        results = data.get("results", [])
        
        if not results:
            logger.warning(f"No event found with ID: {event_id}")
            return None
            
        logger.info(f"Retrieved details for event {event_id}")
        return results[0]
    
    def clear_cache(self):
        """Clear the LRU cache."""
        if hasattr(self.fetch_events, 'cache_clear'):
            self.fetch_events.cache_clear()
            logger.info("Cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if hasattr(self.fetch_events, 'cache_info'):
            info = self.fetch_events.cache_info()
            return {
                "hits": info.hits,
                "misses": info.misses,
                "maxsize": info.maxsize,
                "currsize": info.currsize
            }
        return {}