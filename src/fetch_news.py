import os
import time
from typing import List, Dict, Iterable


import requests
import feedparser


from src.utils import logger
from src.config import NEWSAPI_KEY


NEWSAPI_URL = "https://newsapi.org/v2/everything"




def _requests_get_with_backoff(url: str, params: Dict = None, max_tries: int = 3, timeout: int = 15):
    delay = 1.0
    for attempt in range(1, max_tries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            logger.warning("Request attempt %s failed: %s", attempt, exc)
            if attempt == max_tries:
                raise
            time.sleep(delay)
            delay *= 2.0




def fetch_newsapi(query: str, page: int = 1, page_size: int = 20) -> List[Dict]:
    if not NEWSAPI_KEY:
        raise RuntimeError("NEWSAPI_KEY not set in environment")
    params = {
        "q": query,
        "page": page,
        "pageSize": page_size,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWSAPI_KEY,
    }
    resp = _requests_get_with_backoff(NEWSAPI_URL, params=params)
    data = resp.json()
    articles = data.get("articles", [])
    logger.info("fetch_newsapi: got %s articles", len(articles))
    return _normalize_articles(articles)




def fetch_rss(feed_url: str, max_items: int = 50) -> List[Dict]:
    d = feedparser.parse(feed_url)
    entries = d.get("entries", [])[:max_items]
    logger.info("fetch_rss: got %s entries from %s", len(entries), feed_url)
    return _normalize_articles(entries)




def _normalize_articles(raw: Iterable[Dict]) -> List[Dict]:
    out = []
    for a in raw:
        out.append({
            "source": (a.get("source", {}) or {}).get("name") if isinstance(a.get("source"), dict) else a.get("source"),
            "title": a.get("title") or a.get("headline"),
            "description": a.get("description") or a.get("summary"),
            "content": a.get("content") or a.get("summary") or "",
            "url": a.get("url") or a.get("link"),
            "published_at": a.get("publishedAt") or a.get("published") or "",
        })
    return out