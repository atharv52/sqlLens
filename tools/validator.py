import re

BLOCKED_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE", "REPLACE"]

MAX_RETRIES = 2

def sanitize_sql(query: str) -> str:
    """Strip markdown code fences from LLM-generated SQL."""
    query = re.sub(r"```sql", "", query)
    query = re.sub(r"```", "", query)
    return query.strip()

def check_blocked_keywords(query: str) -> None:
    """Raise an error if the query contains any dangerous SQL keywords."""
    upper_query = query.upper()
    for keyword in BLOCKED_KEYWORDS:
        # Word boundary check — avoids false positives like 'CREATED_AT'
        if re.search(rf"\b{keyword}\b", upper_query):
            raise ValueError(
                f"Query blocked: '{keyword}' statements are not permitted. "
                f"Only SELECT queries are allowed."
            )


def validate_query(query: str) -> str:
    """
    Validate SQL query before execution.
    Returns the cleaned query if valid, raises ValueError if not.
    """
    query = query.strip()

    if not query:
        raise ValueError("Empty query received.")

    check_blocked_keywords(query)

    if not re.match(r"^\s*SELECT", query, re.IGNORECASE):
        raise ValueError(
            f"Query blocked: Only SELECT statements are permitted. "
            f"Received query starting with: '{query[:50]}'"
        )

    return query


def execute_with_retry(query: str, execute_fn, max_retries: int = MAX_RETRIES) -> str:
    """
    Execute a SQL query with retry logic.
    On failure, passes the error back so the agent can self-correct.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            validate_query(query)
            result = execute_fn(query)
            return result
        except ValueError as e:
            # Validation failure — no point retrying, return immediately
            return f"Validation Error: {e}"
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                print(f"[Retry {attempt}/{max_retries}] Query failed: {last_error}")
            else:
                return (
                    f"Query failed after {max_retries} attempts. "
                    f"Last error: {last_error}. "
                    f"Please rewrite the query."
                )

    return f"Unexpected failure. Last error: {last_error}"