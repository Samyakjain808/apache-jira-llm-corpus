#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.run --projects HADOOP --since 2024-01-01 --out output --max-issues 50
python -m src.validate_corpus --path output/corpus/apache_jira_corpus.jsonl --schema schema/corpus.schema.json
echo "Done. Sample at output/corpus/apache_jira_corpus.jsonl"
