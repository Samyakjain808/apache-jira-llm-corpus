from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional
import httpx
import backoff
import logging

DEFAULT_HEADERS = {
    "User-Agent": "ApacheJiraCorpusBot/1.0 (+https://github.com/your-org)"
}

log = logging.getLogger("jira")

class JiraClient:
    def __init__(self, base_url: str, timeout_s: int = 15, min_delay_ms=250, max_delay_ms=1500, max_retries=8):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout_s, headers=DEFAULT_HEADERS)
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self.max_retries = max_retries

    def _polite_sleep(self):
        time.sleep(random.uniform(self.min_delay_ms, self.max_delay_ms) / 1000.0)

    def _backoff_hdlr(self, details):
        log.warning("Retrying %s: try %s, wait %.2fs", details.get("target"), details.get("tries"), details.get("wait"))

    def _giveup(self, e: Exception):
        if isinstance(e, httpx.HTTPStatusError):
            status = e.response.status_code
            return 400 <= status < 500 and status != 429
        return False

    @backoff.on_exception(
        backoff.expo,
        (httpx.TransportError, httpx.ReadTimeout, httpx.HTTPStatusError),
        max_tries=8,
        giveup=_giveup,
        on_backoff=_backoff_hdlr,
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
            log.warning("429 received. Sleeping for %ss", delay)
            time.sleep(delay)
            resp.raise_for_status()
        resp.raise_for_status()
        return resp

    def search_issues(self, jql: str, start_at=0, max_results=100, fields: Optional[List[str]] = None):
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
        r = self._get(f"/rest/api/2/issue/{key}/comment", {"startAt": start_at, "maxResults": max_results})
        return r.json()
