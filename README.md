# Apache Jira → JSONL Corpus Pipeline (Interview-Ready 🚀)

A **production-grade, fault-tolerant data pipeline** that scrapes public **Apache Jira** projects and converts them into a **clean, LLM-ready JSONL corpus**.  
Built for performance, recoverability, and data quality — complete with tests, CI, schema validation, and Docker support.

---

## 🌟 Highlights

- ⚙️ **Resumable & Fault-Tolerant:** SQLite-based state checkpointing with safe recovery  
- 🔁 **Smart Retries & Backoff:** Handles `429` / `5xx` gracefully with exponential backoff  
- 🧱 **Structured LLM Corpus:** Deterministic JSONL + schema + validator  
- 🧪 **CI-Driven Quality:** Pytest + GitHub Actions (lint, test, style)  
- 🧰 **Pre-commit & Code Quality:** Black • Isort • Flake8  
- 🐳 **Docker-Ready:** Portable and reproducible anywhere  

---

## 🚀 Quickstart

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run scraper for 3 Apache projects (2018+ issues)
python -m src.run --projects HADOOP KAFKA SPARK --since 2018-01-01 --out output

# Output → output/corpus/apache_jira_corpus.jsonl
````

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
