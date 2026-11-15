import os
import time
import random
import requests
from fake_useragent import UserAgent

UA = UserAgent()

def _headers(extra: dict = None, html: bool = False):
    h = {"User-Agent": UA.random, "Accept": "application/json, text/plain, */*"}
    if html:
        h["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        h["Accept-Language"] = "en-US,en;q=0.9"
        h["Cache-Control"] = "no-cache"
    if extra:
        h.update(extra)
    return h

def get_api_key(name: str):
    return os.environ.get(name)

def tron_headers() -> dict:
    key = os.environ.get("TRONSCAN_API_KEY", "").strip()
    if key:
        return {"TRON-PRO-API-KEY": key}
    return {}

def safe_get(url: str, params: dict = None, headers: dict = None, html: bool = False,
             max_retries: int = 5, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=_headers(headers, html=html), timeout=25)
        except requests.RequestException:
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in (401, 403, 429):
            wait = base_delay * (2 ** attempt) + random.uniform(0, 1)
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    pass
            time.sleep(wait)
            continue
        if 500 <= resp.status_code < 600:
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
            continue
        return resp
    return None

def safe_post(url: str, json_body: dict, headers: dict = None,
              max_retries: int = 5, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=json_body, headers=_headers(headers), timeout=25)
        except requests.RequestException:
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in (401, 403, 429):
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
            continue
        if 500 <= resp.status_code < 600:
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
            continue
        return resp
    return None