import re
import feedparser
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.oracleflow.models.signal import Signal
from app.oracleflow.constants import SignalSource, SignalCategory
from app.oracleflow.registry.loader import RegistryLoader
from app.oracleflow.feeds.global_feeds import GLOBAL_FEEDS

logger = logging.getLogger(__name__)

# Prefixes commonly added by feeds that should be stripped for dedup
_STRIP_PREFIXES = re.compile(
    r'^(breaking\s*:\s*|exclusive\s*:\s*|update\s*:\s*|alert\s*:\s*|'
    r'opinion\s*:\s*|analysis\s*:\s*|watch\s*:\s*|developing\s*:\s*)',
    re.IGNORECASE,
)
_NON_ALNUM = re.compile(r'[^a-z0-9\s]')


def _normalize_title(title: str) -> str:
    """Normalize a title for dedup: lowercase, strip prefixes and punctuation."""
    t = title.lower().strip()
    t = _STRIP_PREFIXES.sub('', t).strip()
    t = _NON_ALNUM.sub('', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _title_key(title: str) -> str:
    """Return the first 10 words of a normalized title as a dedup key."""
    words = _normalize_title(title).split()
    return ' '.join(words[:10])


def _estimate_sentiment(title: str, summary: str = '') -> float:
    """Keyword-based sentiment scorer. Returns a value in [-1.0, 1.0]."""
    text = (title + ' ' + (summary or '')).lower()

    positive_words = ['peace', 'agreement', 'growth', 'recovery', 'breakthrough', 'ceasefire',
                      'cooperation', 'aid', 'rescue', 'progress', 'reform', 'victory', 'success',
                      'surge', 'rally', 'boost', 'gain', 'improve', 'resolve', 'support']
    negative_words = ['kill', 'attack', 'crash', 'crisis', 'war', 'bomb', 'death', 'collapse',
                      'threat', 'sanctions', 'strike', 'invasion', 'earthquake', 'flood', 'fire',
                      'ransomware', 'breach', 'hack', 'explosion', 'conflict', 'refugee', 'famine',
                      'recession', 'default', 'plunge', 'shutdown', 'disaster', 'emergency']

    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)

    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 2)  # Range: -1.0 to 1.0


def _is_duplicate(db: Session, title: str) -> bool:
    """Check for duplicate signal by normalized title within the last 24 hours.

    Two-pass approach:
    1. Exact match on the raw title (fast, indexed).
    2. Near-duplicate check using first-10-words key with >85% word overlap.
    """
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    # Pass 1: exact match
    count = db.execute(
        select(func.count()).select_from(Signal).where(
            Signal.title == title,
            Signal.timestamp >= cutoff_24h,
        )
    ).scalar()
    if count > 0:
        return True

    # Pass 2: near-duplicate via first-10-words key
    key = _title_key(title)
    if not key:
        return False

    like_pattern = f"%{key[:60]}%"
    candidates = db.execute(
        select(Signal.title).where(
            Signal.title.ilike(like_pattern),
            Signal.timestamp >= cutoff_24h,
        ).limit(10)
    ).scalars().all()

    norm = _normalize_title(title)
    norm_words = set(norm.split())
    if not norm_words:
        return False

    for candidate_title in candidates:
        cand_norm = _normalize_title(candidate_title)
        cand_words = set(cand_norm.split())
        if not cand_words:
            continue
        overlap = len(norm_words & cand_words)
        max_len = max(len(norm_words), len(cand_words))
        similarity = overlap / max_len if max_len else 0
        if similarity > 0.85:
            return True

    return False


def fetch_global_feeds(db: Session, max_per_feed: int = 5) -> list[Signal]:
    """Fetch from all global RSS feeds. This is the main intelligence ingest."""
    signals = []
    errors = 0

    for feed_url, category, source_name in GLOBAL_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            for entry in feed.entries[:max_per_feed]:
                title = (entry.get("title") or "")[:200].strip()
                if not title:
                    continue

                # Dedup by title (exact + near-duplicate)
                if _is_duplicate(db, title):
                    continue

                summary = (entry.get("summary") or "")[:500]
                # Strip HTML tags from summary
                summary = re.sub(r'<[^>]+>', '', summary).strip()

                # Extract entities from title + summary
                from app.oracleflow.entities.signal_extractor import extract_entities
                entities = extract_entities(title, summary)

                raw_data = {
                    "url": entry.get("link", ""),
                    "feed": feed_url,
                    "source_name": source_name,
                    "published": entry.get("published", entry.get("updated", "")),
                }
                if entities:
                    raw_data["entities"] = entities

                signal = Signal(
                    source="rss",
                    signal_type="news_article",
                    category=category,
                    country_code=_guess_country(title + " " + summary),
                    title=title,
                    summary=summary[:400],
                    raw_data_json=raw_data,
                    sentiment_score=_estimate_sentiment(title, summary),
                    anomaly_score=_estimate_anomaly(title + " " + summary),
                    importance=0.5,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(signal)
                signals.append(signal)

        except Exception as e:
            errors += 1
            logger.debug(f"Feed failed [{source_name}] {feed_url}: {e}")
            continue

    db.flush()
    logger.info(f"Global feeds: {len(signals)} new signals from {len(GLOBAL_FEEDS)} feeds ({errors} errors)")
    return signals


def _guess_country(text: str) -> str:
    """Guess country code from text content using keyword matching for 50 countries."""
    t = text.lower()
    country_hints = {
        "JM": ["jamaica", "kingston", "holness", "pnp", "jlp"],
        "TT": ["trinidad", "tobago", "port of spain", "rowley"],
        "BB": ["barbados", "bridgetown", "mottley"],
        "US": ["united states", "washington", "congress", "biden", "trump", "white house", "pentagon", "federal reserve"],
        "GB": ["united kingdom", "britain", "london", "parliament", "downing", "starmer", "sunak"],
        "DE": ["germany", "berlin", "bundestag", "scholz", "merz"],
        "FR": ["france", "paris", "macron", "elysee", "french"],
        "CN": ["china", "beijing", "chinese", "xi jinping"],
        "RU": ["russia", "moscow", "putin", "kremlin", "russian"],
        "JP": ["japan", "tokyo", "japanese", "kishida"],
        "KR": ["south korea", "seoul", "korean", "yoon suk"],
        "AU": ["australia", "canberra", "sydney", "australian", "albanese"],
        "CA": ["canada", "ottawa", "canadian", "trudeau"],
        "BR": ["brazil", "brasilia", "brazilian", "lula", "bolsonaro"],
        "MX": ["mexico", "mexican", "mexico city", "amlo", "sheinbaum"],
        "AR": ["argentina", "buenos aires", "milei", "argentine"],
        "CL": ["chile", "santiago", "chilean", "boric"],
        "CO": ["colombia", "bogota", "colombian", "petro"],
        "ZA": ["south africa", "pretoria", "cape town", "ramaphosa", "anc"],
        "NG": ["nigeria", "abuja", "lagos", "nigerian", "tinubu"],
        "KE": ["kenya", "nairobi", "kenyan", "ruto"],
        "EG": ["egypt", "cairo", "egyptian", "al-sisi"],
        "SA": ["saudi arabia", "riyadh", "saudi", "mbs"],
        "AE": ["united arab emirates", "dubai", "abu dhabi", "emirati", "uae"],
        "IL": ["israel", "tel aviv", "jerusalem", "netanyahu", "israeli"],
        "IR": ["iran", "tehran", "iranian", "khamenei"],
        "IQ": ["iraq", "baghdad", "iraqi"],
        "SY": ["syria", "damascus", "syrian", "assad"],
        "TR": ["turkey", "turkiye", "ankara", "istanbul", "erdogan", "turkish"],
        "UA": ["ukraine", "kyiv", "zelensky", "ukrainian"],
        "PL": ["poland", "warsaw", "polish", "tusk"],
        "IN": ["india", "delhi", "mumbai", "modi", "indian"],
        "BD": ["bangladesh", "dhaka", "bangladeshi"],
        "PK": ["pakistan", "islamabad", "karachi", "pakistani"],
        "AF": ["afghanistan", "kabul", "afghan", "taliban"],
        "MM": ["myanmar", "burma", "yangon", "naypyidaw", "burmese"],
        "TH": ["thailand", "bangkok", "thai"],
        "VN": ["vietnam", "hanoi", "vietnamese"],
        "ID": ["indonesia", "jakarta", "indonesian", "jokowi", "prabowo"],
        "PH": ["philippines", "manila", "filipino", "marcos"],
        "MY": ["malaysia", "kuala lumpur", "malaysian", "anwar ibrahim"],
        "SG": ["singapore", "singaporean"],
        "TW": ["taiwan", "taipei", "taiwanese"],
        "NZ": ["new zealand", "wellington", "auckland"],
        "SE": ["sweden", "stockholm", "swedish"],
        "NO": ["norway", "oslo", "norwegian"],
        "CH": ["switzerland", "bern", "zurich", "swiss"],
        "IT": ["italy", "rome", "italian", "meloni"],
        "ES": ["spain", "madrid", "spanish", "sanchez"],
        "NL": ["netherlands", "amsterdam", "dutch", "hague"],
    }
    for code, keywords in country_hints.items():
        if any(k in t for k in keywords):
            return code
    return ""


def _estimate_anomaly(text: str) -> float:
    """Estimate anomaly score from text urgency keywords."""
    t = text.lower()
    high_urgency = ["breaking", "urgent", "crisis", "emergency", "war", "attack", "killed", "explosion", "crash", "collapse"]
    medium_urgency = ["warns", "threat", "concern", "fears", "spike", "surge", "plunge", "record"]

    score = 0.3  # baseline
    for w in high_urgency:
        if w in t:
            score = max(score, 0.8)
            break
    for w in medium_urgency:
        if w in t:
            score = max(score, 0.6)
            break
    return score


def fetch_country_rss(db: Session, country_code: str) -> list[Signal]:
    """Fetch RSS feeds for a country from registry sources."""
    loader = RegistryLoader()
    country = loader.get_country(country_code)
    if not country:
        return []

    signals = []
    for source in country.sources.news:
        # Try common RSS feed patterns
        clean_url = source.url.replace("https://", "").replace("http://", "")
        rss_urls = [
            f"https://{clean_url}/feed",
            f"https://{clean_url}/rss",
            f"https://{clean_url}/feed/rss",
        ]

        for rss_url in rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                if not feed.entries:
                    continue

                for entry in feed.entries[:10]:
                    title = entry.title[:200] if entry.title else ""
                    if not title:
                        continue

                    # Check if signal already exists (dedup by title)
                    existing = db.execute(
                        select(Signal).where(Signal.title == title)
                    ).scalar_one_or_none()
                    if existing:
                        continue

                    # Extract source name from the feed URL domain
                    try:
                        from urllib.parse import urlparse
                        _host = urlparse(rss_url).hostname or ""
                        _source_name = _host.replace("www.", "").split(".")[0].upper()
                    except Exception:
                        _source_name = source.name if hasattr(source, 'name') else ""

                    _summary = entry.get("summary", "")[:500]

                    # Extract entities from title + summary
                    from app.oracleflow.entities.signal_extractor import extract_entities
                    _entities = extract_entities(title, _summary)

                    _raw_data = {
                        "url": entry.link,
                        "feed": rss_url,
                        "source_name": _source_name,
                        "published": entry.get("published", entry.get("updated", "")),
                    }
                    if _entities:
                        _raw_data["entities"] = _entities

                    signal = Signal(
                        source=SignalSource.SCRAPLING.value,
                        signal_type="news_article",
                        category=_guess_category(
                            title + " " + _summary
                        ),
                        country_code=country_code,
                        title=title,
                        summary=_summary,
                        raw_data_json=_raw_data,
                        sentiment_score=_estimate_sentiment(title, _summary),
                        anomaly_score=_estimate_anomaly(title + " " + _summary),
                        importance=0.5,
                        timestamp=datetime.now(timezone.utc),
                    )
                    db.add(signal)
                    signals.append(signal)

                break  # Found working RSS URL, skip alternatives
            except Exception as e:
                logger.debug(f"RSS fetch failed for {rss_url}: {e}")
                continue

    db.flush()
    return signals


def reprocess_country_codes(db: Session) -> int:
    """Backfill country_code on existing signals that have empty/null country_code.

    Scans title + summary text against keyword maps for 50 countries and updates
    matching rows in-place. Returns the number of signals updated.
    """
    COUNTRY_KEYWORDS = {
        'JP': ['japan', 'tokyo', 'japanese', 'kishida'],
        'CN': ['china', 'beijing', 'chinese', 'xi jinping'],
        'RU': ['russia', 'moscow', 'putin', 'kremlin', 'russian'],
        'UA': ['ukraine', 'kyiv', 'zelensky', 'ukrainian'],
        'IR': ['iran', 'tehran', 'iranian', 'khamenei'],
        'IL': ['israel', 'tel aviv', 'jerusalem', 'netanyahu', 'israeli'],
        'TW': ['taiwan', 'taipei', 'taiwanese'],
        'IN': ['india', 'delhi', 'mumbai', 'modi', 'indian'],
        'BD': ['bangladesh', 'dhaka', 'bangladeshi'],
        'PK': ['pakistan', 'islamabad', 'karachi', 'pakistani'],
        'US': ['united states', 'washington', 'congress', 'biden', 'trump', 'white house', 'pentagon', 'federal reserve'],
        'GB': ['united kingdom', 'britain', 'london', 'parliament', 'downing', 'starmer', 'sunak'],
        'DE': ['germany', 'berlin', 'bundestag', 'scholz', 'merz'],
        'FR': ['france', 'paris', 'macron', 'elysee', 'french'],
        'KR': ['south korea', 'seoul', 'korean', 'yoon suk'],
        'AU': ['australia', 'canberra', 'sydney', 'australian', 'albanese'],
        'CA': ['canada', 'ottawa', 'canadian', 'trudeau'],
        'BR': ['brazil', 'brasilia', 'brazilian', 'lula', 'bolsonaro'],
        'MX': ['mexico', 'mexican', 'mexico city', 'amlo', 'sheinbaum'],
        'AR': ['argentina', 'buenos aires', 'milei', 'argentine'],
        'CL': ['chile', 'santiago', 'chilean', 'boric'],
        'CO': ['colombia', 'bogota', 'colombian', 'petro'],
        'ZA': ['south africa', 'pretoria', 'cape town', 'ramaphosa', 'anc'],
        'NG': ['nigeria', 'abuja', 'lagos', 'nigerian', 'tinubu'],
        'KE': ['kenya', 'nairobi', 'kenyan', 'ruto'],
        'EG': ['egypt', 'cairo', 'egyptian', 'al-sisi'],
        'SA': ['saudi arabia', 'riyadh', 'saudi', 'mbs'],
        'AE': ['united arab emirates', 'dubai', 'abu dhabi', 'emirati', 'uae'],
        'IQ': ['iraq', 'baghdad', 'iraqi'],
        'SY': ['syria', 'damascus', 'syrian', 'assad'],
        'TR': ['turkey', 'turkiye', 'ankara', 'istanbul', 'erdogan', 'turkish'],
        'PL': ['poland', 'warsaw', 'polish', 'tusk'],
        'AF': ['afghanistan', 'kabul', 'afghan', 'taliban'],
        'MM': ['myanmar', 'burma', 'yangon', 'naypyidaw', 'burmese'],
        'TH': ['thailand', 'bangkok', 'thai'],
        'VN': ['vietnam', 'hanoi', 'vietnamese'],
        'ID': ['indonesia', 'jakarta', 'indonesian', 'jokowi', 'prabowo'],
        'PH': ['philippines', 'manila', 'filipino', 'marcos'],
        'MY': ['malaysia', 'kuala lumpur', 'malaysian', 'anwar ibrahim'],
        'SG': ['singapore', 'singaporean'],
        'NZ': ['new zealand', 'wellington', 'auckland'],
        'SE': ['sweden', 'stockholm', 'swedish'],
        'NO': ['norway', 'oslo', 'norwegian'],
        'CH': ['switzerland', 'bern', 'zurich', 'swiss'],
        'IT': ['italy', 'rome', 'italian', 'meloni'],
        'ES': ['spain', 'madrid', 'spanish', 'sanchez'],
        'NL': ['netherlands', 'amsterdam', 'dutch', 'hague'],
        'JM': ['jamaica', 'kingston', 'holness', 'pnp', 'jlp'],
        'TT': ['trinidad', 'tobago', 'port of spain', 'rowley'],
        'BB': ['barbados', 'bridgetown', 'mottley'],
    }

    # Fetch all signals with empty country_code
    stmt = (
        select(Signal)
        .where(
            (Signal.country_code.is_(None)) | (Signal.country_code == '')
        )
    )
    result = db.execute(stmt)
    signals = list(result.scalars().all())

    updated = 0
    for signal in signals:
        text = ((signal.title or '') + ' ' + (signal.summary or '')).lower()
        for code, keywords in COUNTRY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                signal.country_code = code
                updated += 1
                break

    if updated:
        db.flush()

    logger.info("Reprocessed country_codes: %d of %d signals updated", updated, len(signals))
    return updated


def _guess_category(text: str) -> str:
    """Simple keyword-based category detection."""
    text_lower = text.lower()
    if any(
        w in text_lower
        for w in [
            "election",
            "vote",
            "parliament",
            "minister",
            "party",
            "political",
        ]
    ):
        return SignalCategory.POLITICS.value
    if any(
        w in text_lower
        for w in ["gdp", "inflation", "economy", "trade", "export", "import", "tax"]
    ):
        return SignalCategory.ECONOMY.value
    if any(
        w in text_lower
        for w in ["stock", "market", "investor", "bank", "currency", "crypto"]
    ):
        return SignalCategory.FINANCE.value
    if any(
        w in text_lower
        for w in ["hospital", "health", "doctor", "patient", "medical", "disease"]
    ):
        return SignalCategory.HEALTHCARE.value
    if any(
        w in text_lower
        for w in ["climate", "hurricane", "earthquake", "flood", "weather"]
    ):
        return SignalCategory.CLIMATE.value
    if any(
        w in text_lower
        for w in ["crime", "murder", "police", "arrest", "court", "prison"]
    ):
        return SignalCategory.CRIME.value
    if any(
        w in text_lower
        for w in ["cyber", "hack", "breach", "malware", "ransomware"]
    ):
        return SignalCategory.CYBER.value
    return SignalCategory.OTHER.value
