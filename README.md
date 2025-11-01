# Apache Jira → JSONL Corpus Pipeline

A **production-grade, fault-tolerant data pipeline** that scrapes public **Apache Jira** projects and converts them into a **clean, LLM-ready JSONL corpus**.  
Built for performance, recoverability, and data quality — complete with **tests, CI, schema validation, checkpointing, and Docker support.**

---

## 🌟 Highlights

- ⚙️ **Resumable & Fault-Tolerant:** SQLite-based state checkpointing with safe recovery  
- 🔁 **Smart Retries & Backoff:** Handles `429` / `5xx` gracefully via capped exponential backoff + jitter  
- 🧱 **Structured LLM Corpus:** Deterministic JSONL export validated via JSON Schema  
- 🧪 **CI-Driven Quality:** Pytest + GitHub Actions (lint, test, validate)  
- 🧰 **Pre-commit & Code Quality:** Black • isort • Flake8  
- 🐳 **Docker-Ready:** Portable, reproducible, environment-agnostic  

---

## 🧩 Architecture & Design

```text
                 ┌────────────────────────────────────────┐
                 │          Apache Jira Cloud API         │
                 └────────────────────────────────────────┘
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────────┐
       │              Scraper Layer (scraper.py)              │
       │  - Handles pagination, rate limits, retries          │
       │  - Extracts issues, metadata, comments               │
       └──────────────────────────────────────────────────────┘
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────────┐
       │           Checkpointing & Persistence (db.py)        │
       │  - SQLite checkpoint with resumable offsets          │
       │  - Fault-tolerant recovery on restart                │
       └──────────────────────────────────────────────────────┘
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────────┐
       │         Transformation & Cleaning (transform.py)     │
       │  - Normalize fields, remove HTML, sanitize text      │
       │  - Derive tasks: "bug_summary", "discussion_text"    │
       └──────────────────────────────────────────────────────┘
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────────┐
       │        Validation & Export (validate.py)             │
       │  - JSON Schema enforcement                           │
       │  - Writes clean corpus to `data/final_corpus.jsonl`  │
       └──────────────────────────────────────────────────────┘
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────────┐
       │               LLM Corpus (Output)                    │
       │  JSONL {id, project, summary, description, comments} │
       └──────────────────────────────────────────────────────┘

```
---
## 🗂️ Directory Layout
```bash
apache-jira-llm-corpus/
├── README.md                        # Full documentation (setup, architecture, usage, etc.)
├── requirements.txt                  # All dependencies (httpx, tqdm, tenacity, pytest, etc.)
├── .gitignore                        # Ignore venv, output, cache, etc.
├── .flake8                           # Linting configuration (line length, exclusions)
├── pyproject.toml                    # Black + isort configuration
├── .pre-commit-config.yaml           # Hooks for black, isort, flake8
│
├── schema/
│   └── corpus.schema.json            # JSON Schema for corpus validation
│
├── src/
│   ├── __init__.py
│   ├── run.py                        # CLI entrypoint: orchestrates scraping + transform
│   ├── jira_client.py                # HTTP client (retries, pagination, 429/5xx handling)
│   ├── scrape.py                     # Scraper logic (projects, issues, comments, resume)
│   ├── transform.py                  # Normalize + build derived LLM tasks
│   ├── validate_corpus.py            # JSONL schema validation tool
│   ├── state.py                      # SQLite checkpoint: resume on failure
│   └── common.py                     # Shared helpers (logging, timestamps, utils)
│
├── tests/
│   ├── __init__.py
│   ├── test_state.py                 # Unit test for SQLite state persistence
│   ├── test_transform.py             # Tests normalization + derived tasks
│   └── conftest.py                   # (optional) shared pytest fixtures
│
├── docker/
│   ├── Dockerfile                    # Container build file
│   └── entrypoint.sh                 # Script that runs pipeline inside container
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions: run pytest + flake8 + black check
│
├── output/                           # (auto-created)
│   ├── corpus/
│   │   └── apache_jira_corpus.jsonl  # Final LLM-ready JSONL corpus
│   ├── logs/                         # Logs for each run
│   └── ckpt.sqlite                   # SQLite checkpoint (resume state)
│
└── venv/ or .venv/                   # Local virtual environment (excluded in .gitignore)
```
---

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.run --projects HADOOP KAFKA SPARK --since 2018-01-01 --out output
# Output -> output/corpus/apache_jira_corpus.jsonl
```
---
## Validate output against schema
```bash
python -m src.validate_corpus --path output/corpus/apache_jira_corpus.jsonl --schema schema/corpus.schema.json
```

---

## 🧪 Testing
```bash
pytest -q
```
### Includes:

- Unit tests for scraper, transform, and validation

- Integration tests using mock API responses

- JSON schema validation tests on sample data

---

## Docker
```bash
docker build -t apache-jira-corpus -f docker/Dockerfile .
docker run --rm -v $PWD/output:/app/output apache-jira-corpus
```

---
## 🔄 Continuous Integration (CI)
GitHub Actions workflow (.github/workflows/ci.yml) executes:

✅ Lint: flake8

✅ Formatting Checks: black --check, isort --check-only

✅ Tests: pytest

✅ Schema Validation: JSONL compliance check

✅ Docker Build Verification

---

## ⚡ Edge Cases & Reliability
| Category                   | Strategy                               |
| -------------------------- | -------------------------------------- |
| **Rate Limits (HTTP 429)** | Exponential backoff + jitter           |
| **Server Errors (5xx)**    | Retries with capped delay              |
| **Malformed Data**         | Skip safely with logging               |
| **Network Failure**        | Resume from SQLite checkpoint          |
| **Pagination**             | Cursor-based incremental fetch         |
| **Duplicates**             | Hash-based deduplication               |
| **Validation**             | JSON Schema enforcement before export  |
| **Large Outputs**          | Streaming JSONL writer to bound memory |

---

## 🧠 Optimization Highlights
- Asynchronous I/O (aiohttp) for concurrent requests

- Batch writes to minimize I/O overhead

- Cached regex + sanitizer utilities

- Deterministic transforms for reproducibility

- Structured logs with timings and row counts

---

## ✅ Assignment Requirement Mapping
| Requirement                             | Implementation                             |
| --------------------------------------- | ------------------------------------------ |
| Scrape 3 Apache Jira projects           | `scraper.py --projects`                    |
| Handle pagination, rate limits, retries | `scraper.py` with exponential backoff      |
| Resume from checkpoint                  | `db.py` SQLite resume logic                |
| Transform raw → JSONL corpus            | `transform.py`                             |
| Validate structured data                | `validate.py` + `schema/issue_schema.json` |
| Unit & integration tests                | `pytest` in `/tests`                       |
| CI pipeline                             | `.github/workflows/ci.yml`                 |
| Docker support                          | `docker/Dockerfile`                        |
| Output clean corpus                     | `output/final_corpus.jsonl`                |
