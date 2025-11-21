import re
from typing import Optional


from src.utils import logger
from src.config import HYPE_THRESHOLD


PROMO_WORDS = {
"innovative", "leading", "world-class", "revolutionary", "cutting-edge",
"exclusive", "exciting", "amazing", "state-of-the-art", "best-in-class",
"industry-leading", "groundbreaking", "transformative"
}




def _count_numbers(text: str) -> int:
    return len(re.findall(r"\d[\d,\.]*", text))




def _count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))




def information_density(text: Optional[str]) -> float:
    if not text:
        return 0.0
    text = text.strip()
    words = _count_words(text)
    if words == 0:
        return 0.0
    numbers = _count_numbers(text)
    promo_count = sum(1 for w in PROMO_WORDS if w in text.lower())
    density = (numbers / max(1, words)) + max(0.0, (words - promo_count) / words)
    density = min(1.0, density)
    logger.debug("information_density: words=%s numbers=%s promo=%s density=%.3f",
    words, numbers, promo_count, density)
    return density




def is_high_info(text: Optional[str], threshold: float = HYPE_THRESHOLD) -> bool:
    dens = information_density(text)
    return dens >= threshold