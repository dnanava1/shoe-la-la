import json
import requests
from typing import Dict, Any, Optional
from .prompts import SYSTEM_PROMPT, USER_INSTRUCTION_TEMPLATE
from .schema import as_json_schema

OLLAMA_URL = "http://127.0.0.1:11434"

def generate_raw(prompt: str, *, model: str = "llama3.1:8b", system: Optional[str] = None) -> str:
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",           # <— ask for JSON output
        "options": {"temperature": 0}  # <— more deterministic
    }
    if system:
        payload["system"] = system  # Ollama supports a system field
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()

def parse_shopping_intent(text: str, model: str = "llama3.1:8b") -> Dict[str, Any]:
    schema_json = json.dumps(as_json_schema(), ensure_ascii=False)
    prompt = USER_INSTRUCTION_TEMPLATE.format(text=text, schema=schema_json)

    raw = generate_raw(prompt, model=model, system=SYSTEM_PROMPT)

    # Try to isolate the JSON (in case model adds stray chars)
    first = raw.find("{")
    last = raw.rfind("}")
    if first != -1 and last != -1:
        raw = raw[first:last+1]

    try:
        result = json.loads(raw)
        # Clean up empty values from constraints
        if "constraints" in result:
            result["constraints"] = {k: v for k, v in result["constraints"].items() if v not in [None, ""]}
        return result
    except Exception:
        # fallback: minimal safe default
        return {"intent": "search", "shoe_name": "", "constraints": {}}