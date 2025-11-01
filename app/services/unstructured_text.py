# app/services/unstructured_text.py
import requests
import pandas as pd
import os, json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def sentiment_simple(text: str) -> str:
    pos = ["good","great","excellent","happy","love","satisfied","positive","awesome","recommend"]
    neg = ["bad","poor","sad","hate","unsatisfied","negative","awful","disappoint"]
    t = text.lower()
    score = 0
    for p in pos:
        if p in t: score += 1
    for n in neg:
        if n in t: score -= 1
    if score > 0: return "positive"
    if score < 0: return "negative"
    return "neutral"

def summarize_with_ollama(text: str, timeout=120):
    prompt = f"Summarize in one sentence:\n\n{text}\n\nOne-sentence summary:"
    try:
        r = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=timeout)
        r.raise_for_status()
        return r.json().get("response","").strip()
    except Exception:
        return text[:200]

def analyze_text_column(df, text_col: str, add_summary: bool = True, add_sentiment: bool = True):
    res = df.copy()
    if add_sentiment:
        res[f"{text_col}_sentiment"] = res[text_col].astype(str).apply(sentiment_simple)
    if add_summary:
        # Keep summaries short to avoid long LLM calls; do best-effort
        res[f"{text_col}_summary"] = res[text_col].astype(str).apply(lambda t: summarize_with_ollama(t[:150]) if t and len(t)>10 else "")
    return res
