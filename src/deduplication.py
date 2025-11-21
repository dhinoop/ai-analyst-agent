import hashlib
from typing import Dict, List
from src.utils import logger


def _safe_text(value):
    """Ensure we return a clean string."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        # Join list items as string
        return " ".join(str(v).strip() for v in value)
    if value is None:
        return ""
    return str(value).strip()


def _text_for_compare(article: Dict) -> str:
    """Build a consistent text string for deduplication."""
    parts = [
        _safe_text(article.get("title")),
        _safe_text(article.get("description")),
        _safe_text(article.get("content")),
    ]
    return " ".join([p for p in parts if p])


def deduplicate(articles: List[Dict]) -> List[Dict]:
    """
    Deduplicate articles based on similarity hash built from title+description+content.
    """
    seen = set()
    unique_articles = []

    for art in articles:
        text = _text_for_compare(art)

        # Create hash of first 250 chars (enough to detect duplication)
        hash_val = hashlib.md5(text[:250].encode("utf-8")).hexdigest()

        if hash_val not in seen:
            seen.add(hash_val)
            unique_articles.append(art)

    logger.info("Deduplication: Reduced %s → %s articles", len(articles), len(unique_articles))
    return unique_articles
