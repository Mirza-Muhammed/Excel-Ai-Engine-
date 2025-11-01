# 📊 Excel-AI Engine — LLM Powered Excel Data Intelligence System

### ✨ Natural-Language Data Analysis | Excel Automation | AI-Driven Insights

> Upload any Excel file → Ask questions in English → Get SQL-like results, summaries, pivots, filters, joins & insights powered by LLMs.

---

## 🚀 Key Features

| Capability | Details |
|---|---|
🧠 LLM-Powered Query Understanding | Convert natural language into structured data ops  
📁 Excel File Upload | Works with any `.xlsx` file  
📊 Structured Data Analysis | Filters, aggregations, joins, pivots, math ops  
📅 Date Operations | Extract year/month/day, time diff  
🗣️ Optional Text Intelligence | Summaries, sentiment (LLM-based)  
🖧 REST APIs | `/upload`, `/query/run`  
⚙️ Local AI | Works fully offline via **Ollama + LLaMA3**  
💡 Auto Sample Excel Generator | 1000+ rows structured and unstructured data 

---


## 🧠 Tech Stack

| Component | Tool |
|---|---|
Language | Python 3.10+
Backend | FastAPI
Compute | Pandas, OpenPyXL
LLM | Ollama — LLaMA3
Runtime | Uvicorn
Mode | CLI + REST API

---

## 🏗 System Architecture

```mermaid
flowchart TD
    A[User Request] --> B[FastAPI Server]
    B --> C[LLM - Ollama LLaMA3]
    C -->|JSON plan| D[Query Planner]
    D --> E[Pandas Engine]
    E --> F[Excel I/O]
    F --> G[Final Response]

