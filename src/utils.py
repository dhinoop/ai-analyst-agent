import json
import logging
import time
from typing import Any, Dict


logging.basicConfig(
level=logging.INFO,
format="%(asctime)s — %(levelname)s — %(message)s",
)


logger = logging.getLogger("analyst_agent")




def now_ms() -> int:
    return int(time.time() * 1000)




def safe_parse_json(text: str) -> Dict[str, Any]:
    """Try to parse a JSON-like string, return empty dict on failure."""
    try:
        return json.loads(text)
    except Exception:
# attempt to extract first JSON substring
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                logger.exception("safe_parse_json failed to parse inner JSON")
    return {}