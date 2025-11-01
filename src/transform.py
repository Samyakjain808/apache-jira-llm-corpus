from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .common import html_to_text, safe_get


def normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    f = issue.get("fields", {})
    desc_html = f.get("description")
    comments = issue.get("__comments", [])

    return {
        "source": "apache_jira",
        "key": issue.get("key"),
        "project": safe_get(f, "project", "key"),
        "title": f.get("summary", ""),
        "issuetype": safe_get(f, "issuetype", "name"),
        "status": safe_get(f, "status", "name"),
        "priority": safe_get(f, "priority", "name"),
        "labels": f.get("labels", []) or [],
        "assignee": safe_get(f, "assignee", "displayName"),
        "reporter": safe_get(f, "reporter", "displayName"),
        "created": f.get("created"),
        "updated": f.get("updated"),
        "description_text": html_to_text(desc_html),
        "comments_text": [html_to_text(safe_get(c, "body")) for c in comments],
    }


def to_tasks(issue: Dict[str, Any]) -> List[Dict[str, Any]]:
    body = (issue.get("description_text") or "").strip()
    comments_txt = "\n\n".join(issue.get("comments_text") or [])
    context = (body + ("\n\n" + comments_txt if comments_txt else "")).strip()

    tasks = []
    if context:
        tasks.append(
            {
                "task": "summarization",
                "instruction": "Summarize the following Jira issue discussion in 2-3 sentences.",
                "input": context,
                "target": None,
            }
        )

    if issue.get("priority"):
        tasks.append(
            {
                "task": "classification_priority",
                "instruction": "Classify the issue priority (e.g., Blocker, Critical, Major, Minor, Trivial).",
                "input": context or issue.get("title"),
                "target": issue.get("priority"),
            }
        )
    if issue.get("issuetype"):
        tasks.append(
            {
                "task": "classification_type",
                "instruction": "Classify the issue type (Bug, Improvement, New Feature, Task, etc.).",
                "input": context or issue.get("title"),
                "target": issue.get("issuetype"),
            }
        )

    title = issue.get("title") or ""
    if title and context:
        tasks.append(
            {
                "task": "qa_extractive",
                "instruction": f"Question: What is the main problem described in '{title}'? Answer concisely.",
                "input": context,
                "target": None,
            }
        )

    return tasks


def transform_raw(raw_root: str, out_jsonl: str):
    Path(out_jsonl).parent.mkdir(parents=True, exist_ok=True)
    with open(out_jsonl, "w", encoding="utf-8") as w:
        for p in Path(raw_root).rglob("*.json"):
            try:
                obj = json.loads(p.read_text("utf-8"))
            except Exception:
                continue
            norm = normalize_issue(obj)
            tasks = to_tasks(norm)
            record = {**norm, "tasks": tasks}
            w.write(json.dumps(record, ensure_ascii=False) + "\n")
