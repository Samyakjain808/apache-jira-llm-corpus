from __future__ import annotations
import argparse
import yaml
from pathlib import Path
import logging
import sys

from .jira_client import JiraClient
from .state import State
from .scrape import scrape_project
from .transform import transform_raw

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

def main():
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", nargs="+", default=None, help="Project keys, e.g., HADOOP KAFKA SPARK")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD lower bound for updated")
    ap.add_argument("--out", default="output", help="Output base directory")
    ap.add_argument("--max-issues", type=int, default=0, help="Cap issues per project (0 = unlimited)")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path("config.yaml").read_text("utf-8"))
    base_url = cfg["base_url"]
    projects = args.projects or cfg["projects"]

    search_cfg = cfg.get("search", {})
    since = args.since or search_cfg.get("jql_since")
    fields = search_cfg.get("fields", [])
    max_results = int(search_cfg.get("max_results", 100))

    rl = cfg.get("rate_limit", {})
    storage = cfg.get("storage", {})

    client = JiraClient(
        base_url=base_url,
        timeout_s=int(rl.get("timeout_s", 15)),
        min_delay_ms=int(rl.get("min_delay_ms", 250)),
        max_delay_ms=int(rl.get("max_delay_ms", 1500)),
        max_retries=int(rl.get("max_retries", 8)),
    )

    state = State(storage.get("db_path", "output/checkpoints.sqlite"))

    # SCRAPE
    for prj in projects:
        print(f"\n=== Project {prj} ===")
        n = scrape_project(
            project=prj,
            client=client,
            state=state,
            out_dir=args.out,
            since_date=since,
            fields=fields,
            max_results=max_results,
            max_issues=args.max_issues,
        )
        print(f"Fetched {n} issues for {prj}")

    # TRANSFORM
    raw_root = str(Path(args.out) / "raw")
    out_jsonl = str(Path(args.out) / "corpus" / "apache_jira_corpus.jsonl")
    transform_raw(raw_root, out_jsonl)
    print(f"\nCorpus ready: {out_jsonl}")

if __name__ == "__main__":
    main()
