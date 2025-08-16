# our-crm-ai/api_client.py
from functools import wraps
import json
import os
import time

import requests

API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def retry_api_call(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator to add retry logic for API calls with exponential backoff."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        print(f"❌ API call failed after {max_retries} attempts: {e}")
                        break

                    wait_time = delay * (2**attempt)  # Exponential backoff
                    print(
                        f"⚠️  API call failed (attempt {attempt + 1}), retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)

            raise last_exception

        return wrapper

    return decorator


@retry_api_call()
def make_api_request(method: str, url: str, **kwargs):
    """Enhanced API request wrapper with timeout and retry logic."""
    if "timeout" not in kwargs:
        kwargs["timeout"] = DEFAULT_TIMEOUT
    kwargs["verify"] = True
    if "headers" not in kwargs:
        kwargs["headers"] = HEADERS

    return requests.request(method, url, **kwargs)


def handle_api_error(response):
    """Handles API errors by printing details."""
    print(f"Error: API request failed with status code {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")
