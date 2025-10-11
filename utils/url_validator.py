from functools import lru_cache
import requests

@lru_cache(maxsize=2048)
def validate_url(url: str, timeout: float = 8.0) -> bool:
    try:
        # Try HEAD first
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if 200 <= r.status_code < 300:
            return True
        # Fallback to GET if HEAD blocked
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return 200 <= r.status_code < 300
    except Exception:
        return False



import requests

@lru_cache(maxsize=2048)
def validate_url(url: str, timeout: float = 8.0) -> bool:
    try:
        # Try HEAD first
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if 200 <= r.status_code < 300:
            return True
        # Fallback to GET if HEAD blocked
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return 200 <= r.status_code < 300
    except Exception:
        return False







