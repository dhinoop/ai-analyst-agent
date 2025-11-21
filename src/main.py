import time
from typing import List, Dict
from math import ceil

from src.fetch_news import fetch_newsapi, fetch_rss
from src.deduplication import deduplicate
from src.hype_filter import is_high_info
from src.llm_extraction import extract_batch
from src.export_csv import to_csv
from src.utils import logger
from src.config import HYPE_THRESHOLD

# tunables
BATCH_SIZE = 6  # number of articles per LLM call (adjust based on your quota)
USE_OLLAMA = False  # set to True to use local Ollama if available
MODEL_NAME = None  # default model from env will be used if None


def _textify(value):
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())
    return str(value or "")


def run_pipeline(query: str = "AI startups", pages: int = 1, batch_size: int = BATCH_SIZE, use_ollama: bool = USE_OLLAMA):
    t0 = time.time()
    articles = []
    try:
        for p in range(1, pages + 1):
            articles.extend(fetch_newsapi(query, page=p))
    except Exception as exc:
        logger.warning("Primary fetch failed: %s. Falling back to RSS.", exc)
        articles = fetch_rss("https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", max_items=50)
    fetch_time = time.time() - t0
    logger.info("Fetch latency: %.2fs (%s raw articles)", fetch_time, len(articles))

    # dedupe early
    unique = deduplicate(articles)
    logger.info("Dedupe latency: %.2fs", 0.0)

    # apply hype filter (drop low-info articles early to save tokens)
    filtered = []
    for art in unique:
        summary_text = _textify(art.get("description")) + " " + _textify(art.get("content"))
        if not is_high_info(summary_text, threshold=HYPE_THRESHOLD):
            logger.info("Hype filter: dropping low-info article: %s", art.get("title"))
            continue
        filtered.append(art)

    logger.info("After hype filter: %s articles", len(filtered))

    # Batch the filtered articles into groups and call LLM once per batch
    processed = []
    n = len(filtered)
    if n == 0:
        logger.info("No articles to process after filtering.")
        to_csv(processed)
        return processed

    batches = [filtered[i:i + batch_size] for i in range(0, n, batch_size)]
    llm_total_time = 0.0

    for batch_idx, batch in enumerate(batches, start=1):
        logger.info("Processing batch %s/%s (size=%s)", batch_idx, len(batches), len(batch))
        t0 = time.time()
        # extract_batch returns a list of extraction dicts in same order
        extractions = extract_batch(batch, use_ollama=use_ollama, model=MODEL_NAME)
        batch_time = time.time() - t0
        llm_total_time += batch_time
        logger.info("Batch %s processed in %.2fs", batch_idx, batch_time)

        # merge extracted fields into original article dicts
        for art, ext in zip(batch, extractions):
            merged = {**art, **ext}
            processed.append(merged)

        # optional: small sleep to be nice to API (avoid bursts)
        time.sleep(0.5)

    logger.info("LLM total time: %.2fs for %s processed articles", llm_total_time, len(processed))

    # export result
    csv_path = to_csv(processed)
    logger.info("Pipeline finished. CSV saved at: %s", csv_path)
    return processed


if __name__ == "__main__":
    run_pipeline(query="AI startups", pages=1, batch_size=BATCH_SIZE, use_ollama=USE_OLLAMA)
