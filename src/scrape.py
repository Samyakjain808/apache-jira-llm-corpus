from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
import json
from tqdm import tqdm
import logging
import httpx

from .jira_client import JiraClient
from .state import State
from .common import safe_get

log = logging.getLogger("scrape")


def ensure_dir(p: str | Path):
    Path(p).mkdir(parents=True, exist_ok=True)


def scrape_project(
    project: str,
    client: JiraClient,
    state: State,
    out_dir: str,
    since_date: str,
    fields: List[str],
    max_results: int,
    max_issues: int = 0,
):
    raw_dir = Path(out_dir) / "raw" / project
    ensure_dir(raw_dir)
    start_at, last_issue_key, watermark = state.get(project)

    jql_parts = [f"project = {project}", f"updated >= {since_date}"]
    jql = " AND ".join(jql_parts) + " ORDER BY updated ASC"

    total_processed = 0
    pbar = tqdm(desc=f"{project}", unit="issue")

    while True:
        search = client.search_issues(
            jql, start_at=start_at, max_results=max_results, fields=fields
        )
        issues = search.get("issues", [])
        if not issues:
            break

        for issue in issues:
            key = issue.get("key")

            # Fetch full issue; skip if restricted
            try:
                full = client.get_issue(key)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (401, 403):
                    log.warning("Skipping restricted issue %s (status %s)", key, status)
                    continue
                raise

            # Fetch comments with pagination; skip if restricted
            comments_all: List[Dict[str, Any]] = []
            c_start = 0
            while True:
                try:
                    comments_page = client.get_comments(key, start_at=c_start, max_results=100)
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (401, 403):
                        log.warning("Skipping comments for %s (status %s)", key, status)
                        break
                    raise

                c_total = comments_page.get("total", 0)
                page_comments = comments_page.get("comments", []) or []
                comments_all.extend(page_comments)
                c_start += len(page_comments)
                if c_start >= c_total or len(page_comments) == 0:
                    break

            full["__comments"] = comments_all

            # Write snapshot
            snap_path = raw_dir / f"{key}.json"
            with open(snap_path, "w", encoding="utf-8") as f:
                json.dump(full, f, ensure_ascii=False)

            pbar.update(1)
            total_processed += 1
            last_issue_key = key
            updated = safe_get(full, "fields", "updated", default=None)
            state.update(project, start_at, last_issue_key, updated)

            if max_issues and total_processed >= max_issues:
                pbar.close()
                return total_processed

        start_at += len(issues)
        state.update(project, start_at, last_issue_key, watermark)

    pbar.close()
    return total_processed
