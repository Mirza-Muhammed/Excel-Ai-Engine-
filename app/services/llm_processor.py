import os
import re
import json

# Check and load OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
USE_OPENAI = bool(OPENAI_API_KEY)

if USE_OPENAI:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
    except Exception:
        USE_OPENAI = False


def interpret_query(query: str) -> dict:
    """
    Interpret a natural language query into a structured JSON operation
    for Pandas DataFrame processing.
    """
    q = query.strip().lower()

    # --- Math Operations ---
    if 'add' in q or '+' in q:
        m = re.search(r"add\s+(\w+)\s+(?:and|&)\s+(\w+)(?:\s+as\s+(\w+))?", q)
        if m:
            a, b, new = m.group(1), m.group(2), m.group(3) or f"{m.group(1)}_plus_{m.group(2)}"
            return {"type": "math", "op": "+", "columns": [a, b], "new_column": new}

    # --- Average / Mean ---
    if 'average' in q or 'mean' in q:
        m = re.search(r"average\s+(\w+)\s+by\s+(\w+)", q)
        if m:
            val, grp = m.group(1), m.group(2)
            return {"type": "aggregation", "method": "groupby_agg", "groupby": [grp], "agg": {val: 'mean'}}

    # --- Sum / Total ---
    if 'sum' in q or 'total' in q:
        m = re.search(r"(sum|total)\s+of\s+(\w+)\s+by\s+(\w+)", q)
        if m:
            val, grp = m.group(2), m.group(3)
            return {"type": "aggregation", "method": "groupby_agg", "groupby": [grp], "agg": {val: 'sum'}}

    # --- Filter Queries ---
    if 'filter' in q or 'where' in q or 'greater' in q or 'less' in q:
        m = re.search(r"where\s+(.+)", q)
        if m:
            expr = m.group(1)
            expr = expr.replace('greater than', '>').replace('less than', '<').replace('equals', '==')
            expr = expr.replace(' and ', ' & ').replace(' or ', ' | ')
            return {"type": "filter", "expr": expr}

    # --- Pivot Table ---
    if 'pivot' in q:
        m = re.search(r"pivot\s+(\w+)\s+by\s+(\w+)\s+and\s+(\w+)", q)
        if m:
            values, idx, cols = m.group(1), m.group(2), m.group(3)
            return {"type": "pivot", "index": [idx], "columns": [cols], "values": values, "aggfunc": "sum"}

    # --- Date Extraction ---
    if 'month' in q or 'year' in q or 'day' in q:
        m = re.search(r"extract\s+(month|year|day)\s+from\s+(\w+)(?:\s+as\s+(\w+))?", q)
        if m:
            part, col, new = m.group(1), m.group(2), m.group(3) or f"{col}_{part}"
            return {"type": "date_extract", "column": col, "part": part, "new_column": new}

    # --- Fallback to OpenAI LLM ---
    if USE_OPENAI:
        prompt = (
            "You are an assistant that converts natural language requests about a pandas DataFrame "
            "into a JSON operation. Respond ONLY with JSON describing one operation such as "
            "aggregation, filter, math, pivot, unpivot, date_extract, or join.\n\n"
            f"User request: {query}"
        )

        resp = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=300
        )

        text = resp.choices[0].text.strip()
        try:
            return json.loads(text)
        except Exception:
            raise ValueError('OpenAI returned invalid JSON.')

    # --- If nothing matched ---
    raise ValueError('Could not interpret query. Try simpler phrasing or set OPENAI_API_KEY for better parsing.')


# ✅ Wrapper for orchestration usage
def run_llm_interpretation(user_query: str) -> dict:
    """
    Wrapper for orchestration or API routes to safely interpret a user query.
    Returns a JSON-like dict with 'status' and 'parsed' or 'error'.
    """
    try:
        result = interpret_query(user_query)
        return {"status": "ok", "parsed": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
