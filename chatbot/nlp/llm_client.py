import requests
import json
import os

# Host configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

# Default system prompt for the shopping intent parser
SYSTEM_PROMPT = """
You are a shopping intent extraction assistant.
Extract structured JSON with fields:
- gender
- brand
- product
- color
- size
- price_range
Return ONLY valid JSON. No explanations.
"""

# -----------------------------------------------------
# Low-level LLM call using the Ollama /api/chat endpoint
# -----------------------------------------------------
def generate_raw(prompt, model="llama3:latest", system=SYSTEM_PROMPT):
    """
    Sends a user prompt + system prompt to the Ollama /api/chat endpoint.

    Returns raw text output (concatenated across streamed chunks).
    """

    url = f"{OLLAMA_HOST}/api/chat"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        # We want to consume the streaming response
        r = requests.post(url, json=payload, stream=True)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to call Ollama at {url}: {e}")

    # Ollama streams JSON lines; we collect content
    full_response = ""

    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # If Ollama sends malformed line, skip it
            continue

        # Streaming content comes inside message → content
        if "message" in data and "content" in data["message"]:
            full_response += data["message"]["content"]

    return full_response.strip()


# -----------------------------------------------------
# Utility: Safely extract JSON even if text includes noise
# -----------------------------------------------------
def extract_json(text):
    """
    Safely attempts to extract a JSON object from the LLM response.
    If malformed, attempts to fix common issues (e.g., trailing commas).
    """

    text = text.strip()

    # If the entire output is valid JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try: find the first {...} block
    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # If still bad, last fallback: return empty structured fields
    return {
        "gender": None,
        "brand": None,
        "product": None,
        "color": None,
        "size": None,
        "price_range": None
    }


# -----------------------------------------------------
# High-level API: Parse shopping intent
# -----------------------------------------------------
def parse_shopping_intent(user_text, model="llama3:latest"):
    """
    Sends user query to the LLM and returns a structured JSON dict.
    """

    prompt = f"""
    Extract the customer's shopping intent from the following message.
    Return ONLY JSON.

    Message: "{user_text}"
    """

    raw = generate_raw(prompt, model=model, system=SYSTEM_PROMPT)

    parsed = extract_json(raw)
    return parsed
