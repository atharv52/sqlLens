import os
import json
import re
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_groq import ChatGroq
from langchain.tools import tool

from tools.schema_inspector import schema_inspector_tool
from tools.validator import sanitize_sql, execute_with_retry, validate_query



def load_schema_metadata(path: str = "schema_metadata.json") -> str:
    with open(path, "r") as f:
        metadata = json.load(f)

    lines = [
        f"Table: {metadata['table']}",
        f"Description: {metadata['description']}",
        "",
        "Columns:"
    ]
    for col, desc in metadata["columns"].items():
        lines.append(f"  - `{col}`: {desc}")

    return "\n".join(lines)


def create_agent():
    project_id = "fifth-point-413419"
    dataset = "sqlLens"
    table_name = "telecom_churn"

    db = SQLDatabase.from_uri(
        f"bigquery://{project_id}/{dataset}",
        include_tables=[table_name],
    )

    original_query_tool = QuerySQLDataBaseTool(db=db)

    @tool("sql_db_query", return_direct=False)
    def sanitized_validated_query_tool(query: str) -> str:
        """
        Execute a SQL query against the database.
        Input must be a raw SELECT SQL query — no markdown, no code fences.
        Blocked keywords: DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE, REPLACE.
        """
        clean_query = sanitize_sql(query)
        return execute_with_retry(
            query=clean_query,
            execute_fn=original_query_tool.run,
        )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    schema_context = load_schema_metadata()

    prefix = f"""You are an expert data analyst working with a BigQuery telecom churn dataset.

The table is referenced as sqlLens.telecom_churn — no backticks needed around the table name.
Column names with spaces must use backticks e.g. `International plan`, `Total day minutes`.

IMPORTANT RULES:
1. When providing SQL to any tool, provide ONLY raw SQL — never wrap in markdown or triple backticks.
2. Before writing SQL, use the schema_inspector tool if you are unsure what a column means.
3. Only SELECT queries are allowed. Never write DROP, DELETE, INSERT, UPDATE, ALTER, or CREATE.
4. If a query fails, read the error carefully and rewrite the query to fix it.

Here is the full schema context for reference:

{schema_context}

Always write valid BigQuery SQL.
"""

    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        prefix=prefix,
        agent_type="zero-shot-react-description",
        extra_tools=[sanitized_validated_query_tool, schema_inspector_tool],
    )

    return agent