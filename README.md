# URLHaus Threat Intelligence ETL Pipeline

A modular Python ETL pipeline that ingests malicious URL data from the
[abuse.ch URLHaus](https://urlhaus.abuse.ch/) database, cleans and transforms
the data, performs concurrent DNS enrichment, and stores the final results
in a SQLite database.

The project follows a **Medallion Architecture**:

```
URLHaus CSV
     │
     ▼
┌─────────────┐
│  Ingestion  │
└──────┬──────┘
       ▼
┌─────────────┐
│   Bronze    │
│ Raw/Clean   │
└──────┬──────┘
       ▼
┌─────────────┐
│   Silver    │
│ Transform   │
└──────┬──────┘
       ▼
┌─────────────┐
│ Enrichment  │
│  DNS IPv4   │
└──────┬──────┘
       ▼
┌─────────────┐
│    Gold     │
│   SQLite    │
└─────────────┘
````

---

## 1. Project Objectives

The pipeline performs the following operations:

1. Download the latest URLHaus CSV data.
2. Store the original file in the raw layer.
3. Remove URLHaus metadata comments from the CSV.
4. Load cleaned records into the Bronze layer.
5. Extract URLs from Bronze data.
6. Extract domain/hostname from URLs.
7. Validate domains using regular expressions.
8. Remove invalid/noisy domains.
9. Remove duplicate domains.
10. Resolve domains to IPv4 addresses.
11. Perform DNS lookups concurrently using threads.
12. Handle DNS failures without stopping the pipeline.
13. Store enriched records in the Gold database.
14. Perform idempotent UPSERT operations.
15. Provide offline unit tests.
16. Run the complete pipeline using Docker Compose.

---

# 2. Architecture

## Medallion Architecture

### Ingestion

Downloads the URLHaus CSV dataset from abuse.ch.

```text
URLHaus
   │
   ▼
data/raw/urlhaus.csv
```

The raw file is preserved before transformation.

---

## Bronze Layer

The Bronze stage removes URLHaus metadata/comment lines beginning with `#`
and creates a clean CSV.

```text
data/raw/urlhaus.csv
        │
        ▼
Remove comments
        │
        ▼
data/raw/urlhaus_clean.csv
        │
        ▼
SQLite Bronze table
```

The Bronze layer maintains the structure of the source data as much as
possible without applying business transformations.

---

## Silver Layer

The Silver layer performs parsing and data quality transformations.

### Transformations

* Extract the `url` column.
* Extract hostname/domain from the URL.
* Remove `http://` and `https://`.
* Validate domain format using Regex.
* Remove empty domains.
* Remove `localhost`.
* Remove `127.0.0.1`.
* Remove comment values.
* Remove duplicate domains.

Example:

```text
https://example.com/malware.exe
              │
              ▼
        example.com
```

The result is a sanitized list of unique domains.

---

## Enrichment Layer

The enrichment stage performs IPv4 DNS resolution.

```text
Silver Domain
     │
     ▼
DNS Resolution
     │
 ┌───┴──────────────┐
 ▼                  ▼
IPv4 Found       DNS Failure
 ▼                  ▼
1.2.3.4            NULL
```

DNS resolution is an I/O-bound operation, so the pipeline uses
`ThreadPoolExecutor` to perform multiple DNS lookups concurrently.

### Why threading?

DNS resolution spends most of its time waiting for a network response.

Therefore, threads allow multiple domains to be processed while other
requests are waiting.

```text
Domain 1 ──────── DNS ──────────► IP
Domain 2 ─── DNS ─────► IP
Domain 3 ───────────── DNS ─────► IP
Domain 4 ── DNS ─────► IP
```

DNS failures are caught and represented as `NULL` rather than terminating
the pipeline.

---

# 3. Gold Layer

The Gold layer stores the final enriched domain information in SQLite.

Schema:

| Column         | Description                    |
| -------------- | ------------------------------ |
| `domain`       | Domain name and Primary Key    |
| `resolved_ip`  | Resolved IPv4 address          |
| `last_updated` | Timestamp of the latest update |

Example:

```text
domain          resolved_ip       last_updated
------------------------------------------------
example.com     93.184.216.34     2026-08-28 ...
example.org     93.184.216.35     2026-08-28 ...
```

---

## Idempotent UPSERT

The Gold layer uses an UPSERT strategy.

If the domain does not exist:

```text
INSERT
```

If the domain already exists:

```text
UPDATE
```

Example:

### First pipeline run

```text
example.com → 1.2.3.4
```

### Second pipeline run

```text
example.com → 5.6.7.8
```

The database contains only:

```text
example.com → 5.6.7.8
```

No duplicate record is created.

Therefore, running the pipeline multiple times produces a consistent
database state.

---

# 4. Project Structure

```text
threatIntelligenceETLPipeline/
│
├── ingestion/
│   └── download_urlhaus.py
│
├── bronze/
│   └── raw_ingestions_of_files_to_bronze.py
│
├── silver/
│   └── transform_silver.py
│
├── enrichment/
│   └── dns_resolution.py
│
├── gold/
│   └── load_gold.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_bronze.py
│   ├── test_silver.py
│   ├── test_dns_resolution.py
│   └── test_gold.py
│
├── data/
│   ├── raw/
│   └── bronze/
│
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── LICENSE
└── README.md
```

---

# 5. Application Entry Point

The complete pipeline is orchestrated from:

```text
main.py
```

Execution order:

```text
main.py
   │
   ├── 1. Ingestion
   │
   ├── 2. Bronze
   │
   ├── 3. Silver
   │
   ├── 4. DNS Enrichment
   │
   └── 5. Gold
```

Each stage is implemented as a separate Python module.

This keeps the pipeline modular and makes individual stages easier to test
and maintain.

---

# 6. Technologies

* Python 3.12
* SQLite
* pytest
* unittest.mock
* ThreadPoolExecutor
* Docker
* Docker Compose
* Git / GitHub

---

# 7. Local Setup

## Clone the repository

```bash
git clone <your-repository-url>
cd threatIntelligenceETLPipeline
```

---

## Create virtual environment

Windows:

```bash
python -m venv .venv
```

Activate:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# 8. Run the Pipeline Locally

Run the complete pipeline:

```bash
python main.py
```

The pipeline executes:

```text
Ingestion
    ↓
Bronze
    ↓
Silver
    ↓
DNS Enrichment
    ↓
Gold
```

Individual stages can also be executed independently.

For example:

```bash
python ingestion/download_urlhaus.py
```

or:

```bash
python silver/transform_silver.py
```

---

# 9. Running Tests

The project uses `pytest` for unit testing.

Run all tests:

```bash
pytest -v
```

The tests are designed to run offline.

External dependencies such as:

* HTTP requests
* DNS lookups

are mocked using `unittest.mock`.

This means tests do not depend on the URLHaus service or external DNS servers.

---

# 10. DNS Testing

DNS resolution is tested by mocking:

```python
socket.getaddrinfo
```

Example scenarios tested:

```text
Valid domain
     ↓
IPv4 returned

Invalid/non-existent domain
     ↓
None returned

DNS exception
     ↓
Pipeline continues
```

This prevents tests from depending on real network connectivity.

---

# 11. Database Testing

The Gold layer tests use an in-memory SQLite database:

```text
sqlite3.connect(":memory:")
```

This allows tests to verify:

* Table creation
* Correct schema
* INSERT behavior
* UPDATE behavior
* UPSERT behavior
* Duplicate prevention
* NULL IP handling

without modifying the production database.

---

# 12. Docker

The project includes:

```text
Dockerfile
docker-compose.yml
```

The Docker image contains the complete Python application.

Build the image:

```bash
docker compose build
```

Run the pipeline:

```bash
docker compose up
```

Or build and run together:

```bash
docker compose up --build
```

The Docker container starts:

```text
python main.py
```

which executes the complete ETL pipeline.

---

# 13. Docker Data Persistence

The local `data/` directory is mounted into the Docker container.

```yaml
volumes:
  - ./data:/app/data
```

This allows the SQLite database to persist outside the container.

```text
Host
│
└── data/
      │
      └── SQLite database
             ▲
             │
        Docker volume
             │
             ▼
Container
│
└── /app/data/
```

---

# 14. Error Handling

The pipeline is designed so that failures in individual records do not
terminate the entire pipeline.

For DNS resolution:

```text
DNS Success
    → IPv4 address

DNS Failure
    → NULL
```

The pipeline continues processing the remaining domains.

---

# 15. Data Quality

The Silver layer performs the following quality checks:

```text
Raw URL
   │
   ▼
Extract domain
   │
   ▼
Regex validation
   │
   ▼
Remove empty values
   │
   ▼
Remove localhost
   │
   ▼
Remove 127.0.0.1
   │
   ▼
Remove duplicates
   │
   ▼
Clean domain list
```

---

# 16. Design Decisions

### Why Medallion Architecture?

Separating the pipeline into Bronze, Silver, and Gold layers provides clear
responsibilities for each stage.

### Why SQLite?

SQLite is lightweight, serverless, and suitable for this local ETL project.
It also allows the complete pipeline to run without requiring a separate
database server.

### Why ThreadPoolExecutor?

DNS lookups are I/O-bound. Threading allows multiple DNS requests to execute
concurrently and improves throughput compared with sequential resolution.

### Why UPSERT?

The pipeline may be executed repeatedly. UPSERT ensures that existing
domains are updated instead of creating duplicate records.

### Why Mock External Services?

Unit tests should be deterministic and offline. HTTP downloads and DNS
lookups are therefore mocked during testing.

---

# 17. Running the Complete Project

### Local

```bash
python main.py
```

### Tests

```bash
pytest -v
```

### Docker

```bash
docker compose up --build
```

---

# 18. Pipeline Summary

```text
                    URLHaus
                       │
                       ▼
              ┌────────────────┐
              │    Ingestion   │
              └───────┬────────┘
                      │
                      ▼
                 Raw CSV
                      │
                      ▼
              ┌────────────────┐
              │     Bronze     │
              │ Remove # lines │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │     Silver     │
              │ Parse URL      │
              │ Extract Domain │
              │ Regex Validate │
              │ Remove Noise   │
              │ Deduplicate    │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │   Enrichment   │
              │ Concurrent DNS │
              │     IPv4       │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │      Gold      │
              │ SQLite UPSERT  │
              └────────────────┘
```

---

