# SQLens

A natural language SQL agent that lets you query a BigQuery telecom churn dataset using plain English. Built with LangChain, Groq (Llama 3.3 70B), and Google BigQuery.

---

## What it does

- Accepts plain English questions and converts them to valid BigQuery SQL
- Executes queries against a real BigQuery table and returns results
- Uses a schema-aware context layer so the agent understands what each column means before writing SQL
- Validates every query before execution — blocks destructive statements and retries on failure
- Sanitizes LLM output to strip markdown artifacts before hitting the database

---

## Architecture

```
User Question
     │
     ▼
  LangChain Agent (Llama 3.3 70B via Groq)
     │
     ├──► schema_inspector    → looks up column descriptions from schema_metadata.json
     │
     ├──► sql_db_schema       → fetches live table schema from BigQuery
     │
     └──► sql_db_query        → sanitize → validate → execute → retry on failure
               │
               ▼
          Google BigQuery
               │
               ▼
        Structured Result
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Llama 3.3 70B via Groq (free tier) |
| Agent Framework | LangChain |
| Database | Google BigQuery (sandbox — no credit card) |
| Dataset | Telecom Customer Churn |
| Language | Python 3.10+ |

---

## Project Structure

```
sqllens/
├── agent/
│   ├── __init__.py
│   └── sql_agent.py          # core agent — wires LLM, tools, and BQ connection
├── tools/
│   ├── __init__.py
│   ├── schema_inspector.py   # custom tool for column description lookup
│   └── validator.py          # SQL sanitizer, keyword blocker, retry logic
├── schema_metadata.json      # human-readable column descriptions for schema context
├── main.py                   # CLI entry point
├── requirements.txt
└── .env                      # API keys (not committed)
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A [Groq account](https://groq.com) — free tier, no credit card
- A Google account with [BigQuery Sandbox](https://console.cloud.google.com/bigquery) enabled — no credit card

### 2. Clone the repo

```bash
git clone https://github.com/atharv52/sqllens.git
cd sqllens
```

### 3. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/gcp_credentials.json
```

### 6. Set up BigQuery

- Go to [BigQuery Sandbox](https://console.cloud.google.com/bigquery) — no billing required
- Create a dataset named `sqlLens`
- Upload the telecom churn CSV as a table named `telecom_churn`
- Create a GCP Service Account with **BigQuery Data Viewer** + **BigQuery Job User** roles
- Download the JSON key and set its path in `.env`

### 7. Run

```bash
python main.py
```

---

## Example Questions

```
Ask a question: How many customers churned?
Ask a question: What percentage of customers with an international plan churned vs those without?
Ask a question: Rank states by churn rate from highest to lowest
Ask a question: Segment customers into quartiles by total day minutes and show churn rate per quartile
Ask a question: Among customers with more than 3 customer service calls, what percentage churned?
```

---

## Key Features

### Schema-Aware Context Injection
The agent calls a custom `schema_inspector` tool to look up human-readable column descriptions before generating SQL — reducing ambiguity errors on columns like `International plan` or `Account length`.

### Query Validation Layer
Every query goes through a validation step before hitting BigQuery:
- Blocks destructive keywords: `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `CREATE`
- Enforces SELECT-only queries
- Retries up to 2 times on execution failure, passing the error back to the agent for self-correction

### SQL Sanitization
Strips markdown code fences (` ```sql ``` `) from LLM output before execution — prevents syntax errors caused by the model wrapping queries in formatting artifacts.

---

## Security

- Service account scoped to read-only roles — cannot create or delete any GCP resources
- `.env` and `gcp_credentials.json` are gitignored
- No query results are logged or stored

---

## Limitations

- BigQuery Sandbox tables expire after 60 days — re-upload CSV if needed
- Sandbox does not support DML — SELECT only (aligned with this project's design)
- Complex multi-hop analytical questions may require 2-3 retries

---

## Future Improvements

- [ ] Streamlit UI for browser-based interaction
- [ ] Structured JSON output with query explanation
- [ ] Query history and caching
- [ ] Clarification handling for vague questions