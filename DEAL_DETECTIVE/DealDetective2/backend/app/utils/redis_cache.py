import redis
import os
import json
from typing import Optional, Any
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class RedisCache:
    """
    Redis cache utility for caching scraped content and analysis results
    """
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration (default 1 hour)"""
        try:
            serialized = json.dumps(value)
            return self.client.setex(key, expire, serialized)
        except Exception as e:
            print(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting from cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Error checking cache existence: {e}")
            return False


# Global instance for easy access
_cache_instance = None

def get_cache_instance():
    """Get or create Redis cache instance"""
    global _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = RedisCache()
        except Exception as e:
            print(f"Warning: Redis not available: {e}")
            return None
    return _cache_instance

def get_cache(key: str) -> Optional[str]:
    """Get value from cache (returns string, not parsed JSON)"""
    cache = get_cache_instance()
    if cache is None:
        return None
    try:
        return cache.client.get(key)
    except Exception as e:
        print(f"Error getting from cache: {e}")
        return None

def set_cache(key: str, value: str, ttl: int = 3600) -> bool:
    """Set value in cache (accepts string, not JSON)"""
    cache = get_cache_instance()
    if cache is None:
        return False
    try:
        return cache.client.setex(key, ttl, value)
    except Exception as e:
        print(f"Error setting cache: {e}")
        return False

