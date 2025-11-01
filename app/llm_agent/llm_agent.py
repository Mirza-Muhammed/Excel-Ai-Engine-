# app/llm_agent.py
import requests
import os
import json
from typing import Dict, Any

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def call_ollama(prompt: str, timeout: int = 30) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()
    except Exception as e:
        # Ollama down or unreachable
        raise RuntimeError(f"ollama call failed: {e}")

def interpret_nl_to_command(nl: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Try to use Ollama to produce JSON command. If fails, return a simple heuristic JSON.
    """
    prompt = f"""
You are a JSON-only translator. Receive a user query about spreadsheet operations and return ONLY a JSON command.
Schema: {json.dumps(schema or {})}
User query: {nl}
"""
    try:
        out = call_ollama(prompt)
        # some models wrap payloads in text. Try to parse JSON
        try:
            return json.loads(out)
        except Exception:
            # fallback: attempt to extract {...}
            import re
            m = re.search(r"(\{.*\})", out, flags=re.DOTALL)
            if m:
                return json.loads(m.group(1))
            raise
    except Exception:
        # fallback heuristic
        nl2 = nl.lower()
        cmd = {"operation":"filter", "params": {"filter": ""}}
        if "sum" in nl2 or "total" in nl2:
            cmd["operation"] = "aggregate"
            cmd["params"] = {"group_by": [], "aggregations": {}}
        if "pivot" in nl2:
            cmd["operation"] = "pivot"
        return cmd

def analyze_sentiment(text: str) -> str:
    prompt = f"Classify sentiment (Positive/Negative/Neutral). Text: '''{text}'''"
    try:
        out = call_ollama(prompt)
        # return first token
        return out.splitlines()[0].strip()
    except Exception:
        # simple fallback: naive rules
        t = text.lower()
        if any(w in t for w in ["good","excellent","happy","love","great"]):
            return "Positive"
        if any(w in t for w in ["bad","terrible","hate","angry","poor"]):
            return "Negative"
        return "Neutral"
