import urllib.robotparser
from urllib.parse import urlparse
import requests
from starlette.concurrency import run_in_threadpool

# Try to import redis_cache, but don't fail if it's not available
try:
    from app.utils.redis_cache import get_cache, set_cache
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False
    print("Warning: Redis cache not available, robots.txt checks will not be cached")


def _check_robots_sync(target_url: str, robots_url: str, domain: str) -> bool:
    """Synchronous robots.txt check with timeout"""
    # Use requests with timeout to fetch robots.txt, then parse it
    try:
        response = requests.get(robots_url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            # Parse robots.txt content manually to avoid rp.read() which can hang
            robots_content = response.text
            lines = robots_content.split('\n')
            
            # Simple parser: look for "User-agent: *" followed by "Disallow: /"
            in_user_agent_block = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.lower().startswith('user-agent:'):
                    # Check if it's for all agents
                    agent = line.split(':', 1)[1].strip() if ':' in line else ''
                    in_user_agent_block = (agent == '*' or agent == '')
                elif in_user_agent_block and line.lower().startswith('disallow:'):
                    path = line.split(':', 1)[1].strip() if ':' in line else ''
                    # If Disallow: / or Disallow: (empty means disallow all)
                    if path == '/' or path == '':
                        return False
                    # Check if our URL path matches
                    from urllib.parse import urlparse
                    parsed = urlparse(target_url)
                    if parsed.path.startswith(path):
                        return False
            
            # If we get here, no blocking rule found
            return True
        else:
            # If robots.txt doesn't exist (404), usually means public access is OK
            return True
    except requests.exceptions.Timeout:
        print(f"⚠️ Robots.txt check timeout for {domain}, defaulting to blocked")
        return False  # Default to blocked if timeout
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Robots.txt request failed for {domain}: {e}")
        # If robots.txt is missing/broken, usually means public access is OK
        return True
    except Exception as e:
        print(f"⚠️ Robots.txt check error for {domain}: {e}, defaulting to allowed")
        return True  # Default to allowed on error


async def is_allowed(target_url: str) -> bool:
    """
    Checks robots.txt. Returns True if scraping is allowed.
    Now async with timeout protection.
    """
    parsed = urlparse(target_url)
    domain = parsed.netloc
    robots_url = f"{parsed.scheme}://{domain}/robots.txt"
    
    # 1. Check Cache (Don't spam their server) - if Redis is available
    if REDIS_AVAILABLE:
        try:
            cache_key = f"dd:robots:{domain}"
            cached_decision = get_cache(cache_key)
            if cached_decision:
                return cached_decision == "ALLOWED"
        except Exception:
            pass  # Continue without cache if there's an error

    # 2. Check Real Robots.txt (with timeout)
    try:
        allowed = await run_in_threadpool(_check_robots_sync, target_url, robots_url, domain)
    except Exception as e:
        print(f"⚠️ Robots.txt check failed for {domain}: {e}, defaulting to blocked")
        allowed = False  # Default to blocked on error

    # 3. Cache Decision (24 Hours) - if Redis is available
    if REDIS_AVAILABLE:
        try:
            cache_key = f"dd:robots:{domain}"
            decision = "ALLOWED" if allowed else "DISALLOWED"
            set_cache(cache_key, decision, ttl=86400)
        except Exception:
            pass  # Continue without caching if there's an error
    
    return allowed