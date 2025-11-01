# Apache Jira → JSONL Corpus Pipeline (Interview-Ready)

Production-grade, resumable scraper + transformer for Apache's public Jira projects producing LLM-ready JSONL, with tests, CI, schema validation, and Docker.

**Highlights**
- Robust 429/5xx handling, retries, jitter, timeouts
- Resumable via SQLite
- Deterministic JSONL + schema + validator
- Tests (pytest) + GitHub Actions CI
- Pre-commit (black, isort, flake8)
- Dockerfile

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.run --projects HADOOP KAFKA SPARK --since 2018-01-01 --out output
# Output -> output/corpus/apache_jira_corpus.jsonl
```

## Validate output against schema
```bash
python -m src.validate_corpus --path output/corpus/apache_jira_corpus.jsonl --schema schema/corpus.schema.json
```

## Tests
```bash
pytest -q
```

## Docker
```bash
docker build -t apache-jira-corpus -f docker/Dockerfile .
docker run --rm -v $PWD/output:/app/output apache-jira-corpus
```

## CI
GitHub Actions runs lint + tests on every push.
