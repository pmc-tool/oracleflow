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

# ---------------------------------------------------------------------------
# Source-tier importance mapping
# ---------------------------------------------------------------------------
# Wire services get the highest importance; major outlets next; specialized
# domain sources (cyber, crypto, commodities) follow; regional outlets and
# everything else get progressively lower defaults.

SOURCE_TIERS: dict[str, float] = {
    # Wire services — 0.9
    "Reuters World": 0.9, "Reuters Business": 0.9,
    "AP": 0.9, "AFP": 0.9, "UPI": 0.9,
    # Major global outlets — 0.8
    "BBC World": 0.8, "BBC Business": 0.8, "BBC Politics": 0.8,
    "BBC Health": 0.8, "BBC Tech": 0.8,
    "CNN World": 0.8, "CNN Money": 0.8,
    "NPR World": 0.8, "Al Jazeera": 0.8,
    "Guardian World": 0.8, "Guardian Politics": 0.8, "Guardian Climate": 0.8,
    "CNBC": 0.8, "MarketWatch": 0.8, "Yahoo Finance": 0.8,
    "Financial Times": 0.8, "The Economist": 0.8, "WSJ via Dow Jones": 0.8,
    "Foreign Policy": 0.8, "Foreign Affairs": 0.8,
    "ABC News Intl": 0.8, "NBC News World": 0.8, "CBS News World": 0.8,
    "PBS NewsHour World": 0.8,
    "Nikkei Asia": 0.8, "South China Morning Post": 0.8,
    "Deutsche Welle": 0.8, "France 24": 0.8, "NHK World": 0.8,
    "ABC Australia": 0.8, "CBC World": 0.8, "Le Monde": 0.8,
    "El Pais": 0.8, "Der Spiegel Intl": 0.8, "Euronews": 0.8,
    # Specialized domain sources — 0.75
    "CoinDesk": 0.75, "Cointelegraph": 0.75, "Blockworks": 0.75,
    "Decrypt": 0.75, "Bitcoin Magazine": 0.75,
    "Krebs on Security": 0.75, "CISA Advisories": 0.75, "CISA": 0.75,
    "Dark Reading": 0.75, "Schneier": 0.75,
    "BleepingComputer": 0.75, "The Record": 0.75, "SecurityWeek": 0.75,
    "The Hacker News": 0.75, "Cisco Talos": 0.75, "Palo Alto Unit42": 0.75,
    "US-CERT Alerts": 0.75, "NVD CVEs": 0.75,
    "Google Project Zero": 0.75, "Microsoft Security Response": 0.75,
    "GitHub Security Advisories": 0.75,
    "Defense News": 0.75, "Military Times": 0.75, "USNI News": 0.75,
    "Breaking Defense": 0.75, "Janes": 0.75, "Defense One": 0.75,
    "RAND Corporation": 0.75, "Carnegie Endowment": 0.75,
    "Chatham House": 0.75, "Crisis Group": 0.75, "IISS": 0.75,
    "Brookings": 0.75, "Atlantic Council": 0.75, "CSIS": 0.75, "CFR": 0.75,
    "Kitco Gold": 0.75, "OilPrice": 0.75,
    "NASA Climate": 0.75, "CDC": 0.75, "WHO Alerts": 0.75,
    "IMF News": 0.75, "Federal Reserve": 0.75, "ECB Press": 0.75,
    "UN News": 0.75, "IAEA": 0.75, "FAO News": 0.75,
    "State Dept": 0.75, "Pentagon": 0.75, "White House": 0.75,
    "OPEC News": 0.75, "IEA": 0.75, "EIA": 0.75, "EIA Main": 0.75,
    "USDA": 0.75, "CFTC": 0.75,
    "ReliefWeb": 0.75, "UNHCR News": 0.75, "ICRC": 0.75,
    "FEMA": 0.75, "GDACS": 0.75,
    "FreightWaves": 0.75, "Supply Chain Dive": 0.75,
    "Lloyd's List": 0.75, "Journal of Commerce": 0.75,
    # Regional outlets — 0.6
    "Jamaica Observer": 0.6, "Jamaica Gleaner": 0.6, "Loop Jamaica": 0.6,
    "Trinidad Newsday": 0.6, "Trinidad Guardian": 0.6, "Barbados Today": 0.6,
    "Jamaica Gleaner Alt": 0.6, "Trinidad Express": 0.6,
    "Times of India": 0.6, "The Hindu": 0.6, "Indian Express": 0.6,
    "Bangkok Post": 0.6, "VnExpress": 0.6, "Channel NewsAsia": 0.6,
    "Japan Today": 0.6, "Kyiv Independent": 0.6, "Moscow Times": 0.6,
    "Times of Israel": 0.6, "Haaretz": 0.6, "Al Arabiya": 0.6,
    "Miami Herald Americas": 0.6, "MercoPress": 0.6,
    "Buenos Aires Times": 0.6, "Mexico News Daily": 0.6,
    "Africanews": 0.6, "News24 South Africa": 0.6, "AllAfrica": 0.6,
    "Premium Times Nigeria": 0.6, "Vanguard Nigeria": 0.6,
    "Good News Network": 0.6, "Positive News": 0.6,
}

# Default importance for sources not listed above
_DEFAULT_IMPORTANCE = 0.5


def _content_importance(title: str) -> float:
    """Score content importance based on title keywords. Returns adjustment in [-0.05, 0.15]."""
    t = title.lower()
    adjustment = 0.0

    high_keywords = ['breaking', 'urgent', 'exclusive']
    medium_keywords = ['analysis', 'report', 'investigation']
    low_keywords = ['opinion', 'editorial', 'commentary']

    if any(kw in t for kw in high_keywords):
        adjustment += 0.15
    if any(kw in t for kw in medium_keywords):
        adjustment += 0.10
    if any(kw in t for kw in low_keywords):
        adjustment -= 0.05

    return adjustment


def _importance_for_source(source_name: str, title: str = '') -> float:
    """Compute importance from source tier + content keywords, clamped to [0.1, 1.0]."""
    base = SOURCE_TIERS.get(source_name, _DEFAULT_IMPORTANCE)
    adjustment = _content_importance(title) if title else 0.0
    return round(max(0.1, min(1.0, base + adjustment)), 2)


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


try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()

    def _estimate_sentiment(title: str, summary: str = '') -> float:
        """VADER-based sentiment scorer. Returns compound score in [-1.0, 1.0]."""
        text = (title + '. ' + (summary or '')).strip()
        if not text:
            return 0.0
        scores = _vader.polarity_scores(text)
        return round(scores['compound'], 2)
except ImportError:
    def _estimate_sentiment(title: str, summary: str = '') -> float:
        """Keyword-based sentiment scorer (fallback). Returns a value in [-1.0, 1.0].

        Uses stem-prefix matching: each keyword matches any word in the text
        that starts with it (e.g. "threaten" matches "threatens", "threatening").
        """
        text = (title + ' ' + (summary or '')).lower()
        words = text.split()

        positive_keywords = [
            'peace', 'agreement', 'growth', 'recovery', 'breakthrough', 'ceasefire',
            'cooperation', 'aid', 'rescue', 'progress', 'reform', 'victory', 'success',
            'surge', 'rally', 'boost', 'gain', 'improve', 'resolve', 'support',
            'deal', 'agree', 'launch', 'announce', 'expand', 'partner', 'approve',
            'win', 'celebrat', 'open', 'welcome', 'achiev', 'complet', 'develop',
            'innovat', 'invest', 'promot', 'protect', 'strengthen', 'stabiliz', 'recover',
        ]
        negative_keywords = [
            'kill', 'attack', 'crash', 'crisis', 'war', 'bomb', 'death', 'collapse',
            'threat', 'sanction', 'strike', 'invasion', 'earthquake', 'flood', 'fire',
            'ransomware', 'breach', 'hack', 'explosion', 'conflict', 'refugee', 'famine',
            'recession', 'default', 'plunge', 'shutdown', 'disaster', 'emergency',
            'warn', 'threaten', 'fear', 'cut', 'fall', 'decline', 'drop', 'fail',
            'lose', 'suspend', 'block', 'reject', 'oppose', 'delay', 'cancel',
            'violat', 'arrest', 'charge', 'condemn', 'tension', 'dispute',
            'controversy', 'scandal', 'fraud', 'corruption', 'unemploy',
        ]

        def _stem_match(keywords):
            count = 0
            for kw in keywords:
                if any(w.startswith(kw) for w in words):
                    count += 1
            return count

        pos = _stem_match(positive_keywords)
        neg = _stem_match(negative_keywords)

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
                    anomaly_score=_estimate_anomaly(title + " " + summary, source_name=source_name),
                    importance=_importance_for_source(source_name, title),
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


def _estimate_anomaly(text: str, source_name: str = "") -> float:
    """Estimate anomaly score from text urgency keywords with wider spread.

    Scoring bands:
      - Multiple high-urgency keywords: 0.85-1.0
      - Single high-urgency keyword:    0.65-0.80
      - Medium-urgency keyword(s):      0.45-0.65
      - No trigger keywords:            0.15-0.35

    Wire-service sources (importance >= 0.9) get a +0.05 boost.
    """
    t = text.lower()
    high_urgency = [
        "breaking", "urgent", "crisis", "emergency", "war", "attack",
        "killed", "explosion", "crash", "collapse", "invaded", "coup",
        "assassination", "martial law", "catastroph",
    ]
    medium_urgency = [
        "warns", "threat", "concern", "fears", "spike", "surge", "plunge",
        "record", "sanctions", "escalat", "tensions", "protest", "riot",
        "shutdown", "default", "breach", "ransomware", "hack",
    ]

    high_hits = sum(1 for w in high_urgency if w in t)
    medium_hits = sum(1 for w in medium_urgency if w in t)

    if high_hits >= 2:
        # Multiple high-urgency keywords: 0.85 base + up to 0.15 for extra hits
        score = min(1.0, 0.85 + (high_hits - 2) * 0.05)
    elif high_hits == 1:
        # Single high-urgency keyword: 0.65 base + medium keywords add up to 0.15
        score = min(0.80, 0.65 + medium_hits * 0.05)
    elif medium_hits >= 2:
        # Multiple medium keywords: 0.55 base + extras
        score = min(0.65, 0.55 + (medium_hits - 2) * 0.03)
    elif medium_hits == 1:
        # Single medium keyword
        score = 0.45
    else:
        # No trigger keywords — low baseline with slight randomness from text length
        text_len_factor = min(0.1, len(t) / 5000)  # longer text slightly higher
        score = 0.2 + text_len_factor

    # Wire-service boost: sources with importance >= 0.9 get +0.05
    source_importance = _importance_for_source(source_name) if source_name else _DEFAULT_IMPORTANCE
    if source_importance >= 0.9:
        score = min(1.0, score + 0.05)

    return round(score, 2)


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
                        anomaly_score=_estimate_anomaly(title + " " + _summary, source_name=_source_name),
                        importance=_importance_for_source(_source_name, title),
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
