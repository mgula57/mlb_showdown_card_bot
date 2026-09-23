from typing import Any, Dict, Optional
from pydantic import BaseModel, PrivateAttr
import requests
import time
import json
import logging

from ..utils.ttl_cache import TTLCache

# Set up logger
logger = logging.getLogger(__name__)

class BaseMLBClient(BaseModel):
    """Base client providing shared HTTP functionality for all MLB API endpoints"""

    # Client attributes
    base_url: str = "https://statsapi.mlb.com/api/v1"
    timeout: int = 30
    rate_limit_delay: float = 0.2
    use_cache: bool = True
    cache_ttl: int = 300  # 5 minutes default
    max_retries: int = 3
    headers: Dict[str, str] = {}
    session: Any = None
    last_response_from_cache: Optional[bool] = None
    last_response_cache_layer: str = "UNKNOWN"

    # Instance variables for rate limiting and caching
    _cache: TTLCache = PrivateAttr()
    _last_request_time = 0.0

    # -------------------
    # INIT
    # -------------------

    def model_post_init(self, __context):
        """Apply default headers after initialization"""
        default_headers = {
            "User-Agent": "MLBShowdownBot/4.0",
            "Accept": "application/json",
        }
        self.headers = {**default_headers, **self.headers}

        # Clients are typically instantiated once per process (e.g. module-level
        # singletons in the Flask blueprints) and live for the dyno's lifetime, so
        # this must be bounded — a plain dict here grows forever.
        self._cache = TTLCache(ttl_seconds=self.cache_ttl, max_size=1000)

    # -------------------
    # CORE REQUEST LOGIC
    # -------------------

    def _make_request(self, endpoint: str, params: Optional[Dict] = None, cache_override: Optional[bool] = None) -> Dict[str, Any] | list:
        """
        Core HTTP request method with caching, rate limiting, and retries
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            cache_override: Override instance cache setting for this request
            
        Returns:
            JSON response data
        """
        # Clean endpoint
        endpoint = endpoint.lstrip('/')
        
        # Cache key generation
        cache_key = self._generate_cache_key(endpoint, params)
        use_cache = cache_override if cache_override is not None else self.use_cache
        
        # Check cache first
        if use_cache:
            cached_data = self._cache.get(cache_key)
            if cached_data is not None:
                print(f"Cache hit for {endpoint}")
                self.last_response_from_cache = True
                self.last_response_cache_layer = "MEMORY"
                return cached_data
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                data = self._execute_request(endpoint, params)

                # Print curlable URL for debugging
                from urllib.parse import urlencode
                full_url = f"{self.base_url}/{endpoint}"
                if params:
                    full_url += f"?{urlencode(params)}"
                # print(f"curl -g '{full_url}'")

                # Cache successful response
                if use_cache:
                    self._cache_response(cache_key, data)
                
                return data
                
            except requests.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                elif e.response.status_code == 404:
                    # Don't retry 404s
                    raise Exception(f"Endpoint not found: {endpoint}")
                elif attempt == self.max_retries - 1:
                    raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
                else:
                    time.sleep(2 ** attempt)
                    
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def _execute_request(self, endpoint: str, params: Optional[Dict]) -> Dict[str, Any]:
        """Execute the actual HTTP request"""
        url = f"{self.base_url}/{endpoint}"
        
        http_client = self.session if self.session is not None else requests
        response = http_client.get(url, params=params, headers=self.headers, timeout=self.timeout)

        from_cache = bool(getattr(response, "from_cache", False))
        self.last_response_from_cache = from_cache
        self.last_response_cache_layer = "REQUESTS_CACHE" if from_cache else "LIVE"

        response.raise_for_status()
        return response.json()
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict]) -> str:
        """Generate a consistent cache key"""
        if params:
            # Sort params for consistent cache keys
            sorted_params = json.dumps(params, sort_keys=True)
            return f"{endpoint}:{sorted_params}"
        return endpoint
    
    def _cache_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache the response data"""
        self._cache.set(cache_key, data)
        logger.debug(f"Cached response for {cache_key}")
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def clear_cache(self) -> None:
        """Clear all cached responses"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        # __len__ sweeps expired entries first, so this count is always valid entries.
        valid_entries = len(self._cache)
        return {
            'total_entries': valid_entries,
            'valid_entries': valid_entries,
        }