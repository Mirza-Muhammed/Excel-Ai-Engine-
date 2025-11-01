# app/llm_agent/orchestrator.py
import json
import requests
import time
from typing import Dict, Any, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"   # change to smaller model if you pulled one e.g. "llama3:3b"
DEFAULT_TIMEOUT = 600      # seconds (long for slow laptops)

# small in-memory cache for repeated prompts
_llm_cache = {}

class ExcelAIOrchestrator:
    def __init__(self, model: str = DEFAULT_MODEL, ollama_url: str = OLLAMA_URL, timeout: int = DEFAULT_TIMEOUT, fast_mode: bool = False):
        self.model = model
        self.ollama_url = ollama_url
        self.timeout = timeout
        self.fast_mode = fast_mode

    def _call_llm(self, prompt: str) -> str:
        # caching to speed up repeated prompts
        if prompt in _llm_cache:
            return _llm_cache[prompt]
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        resp = requests.post(self.ollama_url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        _llm_cache[prompt] = text
        return text

    def interpret_query(self, user_query: str, columns: Optional[list] = None) -> Dict[str, Any]:
        """
        Returns a dict with keys:
          - operation: aggregate|filter|math|join|pivot|unpivot|date|text|unknown
          - parameters: dict
        The JSON returned follows QueryPayload.params structure used by /query/run.
        """
        # Fast-mode heuristics: avoid LLM for simple common queries
        q = user_query.strip().lower()
        if self.fast_mode:
            if q.startswith("sum ") or q.startswith("total ") or "sum of" in q or "total" in q:
                return {"operation": "aggregate", "parameters": {"agg": "sum", "column": None}}
            if q.startswith("average") or "average" in q or "mean" in q:
                return {"operation": "aggregate", "parameters": {"agg": "mean", "column": None}}
            if q.startswith("filter") or "where" in q:
                return {"operation": "filter", "parameters": {"condition": user_query}}
            # add more heuristics as needed

        # Construct strict prompt to return JSON only
        cols_line = f"Columns: {columns}" if columns else ""
        system_prompt = f"""
You are a JSON-only translator. Convert the user's natural language spreadsheet query into a JSON object with keys:
- operation: one of aggregate|filter|math|join|pivot|unpivot|date|text|unknown
- parameters: an object containing operation-specific keys

Return ONLY valid JSON (no explanation). Example:
{{"operation":"aggregate","parameters":{{"column":"Revenue","agg":"sum","group_by":["Region"]}}}}

{cols_line}
User Query: {user_query}
"""
        try:
            raw = self._call_llm(system_prompt)
            # try to parse JSON direct
            try:
                parsed = json.loads(raw)
                return parsed
            except json.JSONDecodeError:
                # try to extract JSON substring
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    candidate = raw[start:end+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        pass
            # fallback: return unknown
            return {"operation": "unknown", "parameters": {"raw": user_query}}
        except Exception as e:
            # LLM failure fallback
            return {"operation": "unknown", "parameters": {"raw": user_query, "error": str(e)}}
