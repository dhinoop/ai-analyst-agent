import os
import json
import time
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from src.utils import logger, safe_parse_json
from src.config import MAX_SUMMARY_CHARS

# ================================
# OPENAI CLIENT (Optional)
# ================================
try:
    from openai import OpenAI
    _has_openai = True
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _has_openai = False
    _openai_client = None

# ================================
# OLLAMA CONFIG
# ================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST")  # eg: http://localhost:11434
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


# ================================
# HELPER FUNCTIONS
# ================================
def _textify(value) -> str:
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())
    return str(value or "")


def _short_summary(article: Dict[str, Any], max_chars: int = MAX_SUMMARY_CHARS) -> str:
    title = (article.get("title") or "").strip()
    desc = _textify(article.get("description") or "")[:max_chars]
    content = _textify(article.get("content") or "")[:max_chars]

    summary = desc if desc else content
    summary = summary.replace("\n", " ").strip()

    return f"{title} - {summary}"


# ================================
# LLM Prompt
# ================================
BATCH_PROMPT_TEMPLATE = """
You are a JSON-only extractor. Given a numbered list of short news items, 
return a JSON array where each element corresponds to the input article (same order). 
Each element must be an object with exactly these keys:

- company_name (string or null)
- category (string)
- sentiment_score (number between -1 and 1)
- is_funding_news (boolean)

Return ONLY valid JSON. No explanation. No markdown.
"""


# ================================
# OPENAI CALL
# ================================
def _call_openai_batch(items_text: str, model: Optional[str] = None, max_retries: int = 5) -> Optional[str]:
    if not _has_openai or _openai_client is None:
        logger.info("OpenAI not available.")
        return None

    model = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            resp = _openai_client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": BATCH_PROMPT_TEMPLATE + "\n\n" + items_text
                }],
                temperature=0.0,
            )
            return resp.choices[0].message.content

        except Exception as exc:
            logger.warning(f"OpenAI attempt {attempt} failed: {exc}")
            if attempt == max_retries:
                logger.error("OpenAI batch call failed after retries.")
                return None
            time.sleep(backoff)
            backoff *= 2.0


# ================================
# OLLAMA CALL (fixed for streaming JSON)
# ================================
def _call_ollama_batch(items_text: str, max_retries: int = 3) -> Optional[str]:
    if not OLLAMA_HOST:
        return None

    import requests
    url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            # Ollama sends *streaming JSON lines*, not a single JSON!
            resp = requests.post(
                url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": BATCH_PROMPT_TEMPLATE + "\n\n" + items_text,
                    "stream": False  # IMPORTANT: force non-streaming mode
                },
                timeout=60
            )

            resp.raise_for_status()
            data = resp.json()

            # Ollama returns {"response": "...", "done": true}
            return data.get("response")

        except Exception as exc:
            logger.warning(f"Ollama attempt {attempt} failed: {exc}")
            if attempt == max_retries:
                logger.error("Ollama batch call failed after retries.")
                return None
            time.sleep(backoff)
            backoff *= 2.0


# ================================
# MAIN EXTRACTION LOGIC
# ================================
def extract_batch(articles: List[Dict[str, Any]], use_ollama: bool = False, model: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Given a list of article dicts, call the LLM to extract structured info.
    """

    # Build the numbered input list for the model
    lines = []
    for idx, art in enumerate(articles, start=1):
        short = _short_summary(art)
        clean_short = short.replace("\n", " ")
        lines.append(f"{idx}) {clean_short}")

    items_text = "\n".join(lines)

    # ----------------------------
    # TRY OPENAI FIRST
    # ----------------------------
    raw = None
    if not use_ollama and _has_openai:
        raw = _call_openai_batch(items_text, model=model)

    # ----------------------------
    # FALLBACK TO OLLAMA
    # ----------------------------
    if raw is None:
        raw = _call_ollama_batch(items_text)

    parsed_list = []

    # ----------------------------
    # PARSE JSON OUTPUT
    # ----------------------------
    if raw:
        parsed = safe_parse_json(raw)

        if isinstance(parsed, list):
            parsed_list = parsed
        elif isinstance(parsed, dict) and "results" in parsed:
            parsed_list = parsed["results"]

    # ----------------------------
    # BUILD CLEAN OUTPUT
    # ----------------------------
    defaults = {
        "company_name": None,
        "category": "Unknown",
        "sentiment_score": 0.0,
        "is_funding_news": False
    }

    out = []
    for i in range(len(articles)):
        if i < len(parsed_list) and isinstance(parsed_list[i], dict):
            p = parsed_list[i]
            out.append({
                "company_name": p.get("company_name"),
                "category": p.get("category", "Unknown"),
                "sentiment_score": float(p.get("sentiment_score") or 0.0),
                "is_funding_news": bool(p.get("is_funding_news")),
            })
        else:
            out.append(defaults.copy())

    return out
