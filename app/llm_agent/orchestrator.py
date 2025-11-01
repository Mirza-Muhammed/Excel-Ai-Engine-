import os
import json
import time
import threading
import requests
from app.services.orchestrator import orchestrate_user_query


class ExcelAIOrchestrator:
    """
    Orchestrator for Excel AI Engine using a local Ollama LLaMA3 model.
    Handles:
    - Natural language query interpretation
    - Backend API call
    """

    def __init__(self, backend_url="http://127.0.0.1:8000"):
        print("🚀 Initializing ExcelAIOrchestrator (Ollama + LLaMA3)...")
        self.backend_url = backend_url
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3"
        print("✅ Orchestrator ready.")

    # Loading Spinner (Async)
    def _spinner(self, stop_event):
        while not stop_event.is_set():
            for ch in "|/-\\":
                print(f"\r🤖 Thinking {ch}", end="")
                time.sleep(0.1)

    # -------------------------------
    # 1️⃣ Interpret query (LLM)
    # -------------------------------
    def interpret_query(self, user_query: str) -> dict:
        prompt = f"""
        Convert the user query into structured JSON for Excel data operations.
        
        Fields:
        - operation (sum, avg, min, max, filter, join, pivot, etc.)
        - column
        - condition
        - group_by
        - sheet_name
        
        User Query: "{user_query}"
        """

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        stop_event = threading.Event()
        spinner = threading.Thread(target=self._spinner, args=(stop_event,))
        spinner.start()

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            stop_event.set()
            spinner.join()
            print("\r✅ AI interpretation complete")

            result = response.json()
            raw = result.get("response", "").strip()

            try:
                parsed = json.loads(raw)
                print("🧠 Parsed Query:", parsed)
                return parsed
            except json.JSONDecodeError:
                print("⚠️ Couldn't parse proper JSON — Returning text")
                return {"raw_text": raw}

        except Exception as e:
            stop_event.set()
            spinner.join()
            print(f"\n❌ AI error: {e}")
            return {"error": "AI failed", "fallback_operation": "sum"}

    # -------------------------------
    # 2️⃣ Execute backend query
    # -------------------------------
    def execute_query(self, file_path, sheet_name, user_query):
        print("⚙️ Executing request...")
        structured = self.interpret_query(user_query)
        structured["file_path"] = file_path
        structured["sheet_name"] = sheet_name

        try:
            resp = requests.post(f"{self.backend_url}/query/run", json=structured)
            if resp.status_code == 200:
                print("✅ Backend processed successfully")
                return resp.json()
            else:
                print(f"❌ Backend error: {resp.text}")
                return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}


# -------------------------------
# CLI Runner
# -------------------------------
if __name__ == "__main__":
    print("🚀 Starting Excel AI Orchestrator CLI")

    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    excel_files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]

    if not excel_files:
        print("❌ No Excel file found in /data. Upload via /upload/file first.")
        exit(1)

    latest = max(excel_files, key=lambda f: os.path.getmtime(os.path.join(data_dir, f)))
    file_path = os.path.join(data_dir, latest)
    sheet_name = "Structured"

    print(f"📂 Using file: {file_path}")

    while True:
        q = input("\n🧠 Ask: ").strip()
        if q.lower() in ("exit", "quit"):
            print("👋 Bye!")
            break

        engine = ExcelAIOrchestrator()
        out = engine.execute_query(file_path, sheet_name, q)
        print("\n📊 Result:\n", json.dumps(out, indent=2))
