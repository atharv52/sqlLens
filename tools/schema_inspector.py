import json
from langchain.tools import tool


def load_metadata(path: str = "schema_metadata.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)


@tool("schema_inspector", return_direct=False)
def schema_inspector_tool(column_name: str) -> str:
    """
    Use this tool to look up what a column means before writing SQL.
    Pass a column name to get its description, or pass 'all' to get descriptions for every column.
    Always call this when you are unsure what a column represents.
    """
    metadata = load_metadata()
    columns = metadata.get("columns", {})

    if column_name.strip().lower() == "all":
        lines = [f"Table: {metadata['table']}", f"Description: {metadata['description']}", ""]
        for col, desc in columns.items():
            lines.append(f"  - `{col}`: {desc}")
        return "\n".join(lines)

    # Fuzzy match — case insensitive
    for col, desc in columns.items():
        if col.lower() == column_name.strip().lower():
            return f"`{col}`: {desc}"

    # Partial match fallback
    matches = [(col, desc) for col, desc in columns.items()
               if column_name.strip().lower() in col.lower()]

    if matches:
        return "\n".join([f"`{col}`: {desc}" for col, desc in matches])

    return f"Column '{column_name}' not found. Available columns: {', '.join(columns.keys())}"