# src/jira_client.py
from __future__ import annotations

import logging
import random
import time
from typing import Any, Dict, List, Optional

import backoff
import httpx

DEFAULT_HEADERS = {"User-Agent": "ApacheJiraCorpusBot/1.0 (+https://github.com/your-org)"}

log = logging.getLogger("jira")


# ---- module-level helpers (no self!) ----
def giveup_http_error(e: Exception) -> bool:
    """
    Stop retrying on client errors (4xx) EXCEPT 429.
    That includes 401/403 which are often permission-restricted resources.
    """
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        return (400 <= status < 500) and status != 429
    return False


def on_backoff(details):
    wait = details.get("wait", 0.0)
    tries = details.get("tries", 0)
    log.warning("Retrying HTTP call (try %s, wait %.2fs)", tries, wait)


class JiraClient:
    def __init__(
        self, base_url: str, timeout_s: int = 15, min_delay_ms=250, max_delay_ms=1500, max_retries=8
    ):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout_s, headers=DEFAULT_HEADERS)
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self.max_retries = max_retries

    def _polite_sleep(self):
        time.sleep(random.uniform(self.min_delay_ms, self.max_delay_ms) / 1000.0)

    @backoff.on_exception(
        backoff.expo,
        (httpx.TransportError, httpx.ReadTimeout, httpx.HTTPStatusError),
        max_tries=8,
        giveup=giveup_http_error,
        on_backoff=on_backoff,
        jitter=backoff.full_jitter,
    )
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        self._polite_sleep()
        url = f"{self.base_url}{path}"
        resp = self.client.get(url, params=params)
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            delay = 5
            if retry_after:
                try:
                    delay = int(retry_after)
                except Exception:
                    pass
            log.warning("429 Too Many Requests. Sleeping for %ss", delay)
            time.sleep(delay)
            # Raise to trigger backoff chain
            resp.raise_for_status()
        resp.raise_for_status()
        return resp

    def search_issues(
        self, jql: str, start_at=0, max_results=100, fields: Optional[List[str]] = None
    ):
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": ",".join(fields or []),
        }
        r = self._get("/rest/api/2/search", params)
        return r.json()

    def get_issue(self, key: str):
        r = self._get(f"/rest/api/2/issue/{key}")
        return r.json()

    def get_comments(self, key: str, start_at=0, max_results=100):
        r = self._get(
            f"/rest/api/2/issue/{key}/comment", {"startAt": start_at, "maxResults": max_results}
        )
        return r.json()
