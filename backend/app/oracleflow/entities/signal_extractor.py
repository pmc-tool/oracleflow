"""Basic entity extraction for signal titles and summaries.

Extracts financial tickers, CVE identifiers, country references,
key organizations, MITRE ATT&CK techniques, and IOCs from free text.
Designed to run fast with no external dependencies -- pure regex + set lookups.
"""

import re

# ---------------------------------------------------------------------------
# Stop words -- common English words that should never be treated as tickers
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "a", "an", "the", "on", "in", "at", "it", "is", "to", "as", "or", "so",
    "no", "go", "do", "up", "by", "we", "he", "if", "my",
}

# ---------------------------------------------------------------------------
# Financial tickers (commonly referenced in intelligence signals)
# Only tickers with 3+ characters are kept to avoid false positives on
# common English words.  Short-symbol stocks (A, V, C, F, GE, etc.) are
# intentionally excluded.
# ---------------------------------------------------------------------------
TICKER_ALIASES = {
    'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'GOOGLE': 'GOOGL', 'ALPHABET': 'GOOGL',
    'AMAZON': 'AMZN', 'NVIDIA': 'NVDA', 'META': 'META', 'FACEBOOK': 'META',
    'TESLA': 'TSLA', 'NETFLIX': 'NFLX', 'BITCOIN': 'BTC', 'ETHEREUM': 'ETH',
    'OPEC': 'OPEC', 'NATO': 'NATO',  # These are orgs but people search them as tickers
    'OPEC+': 'OPEC',  # OPEC+ variant
    'OIL PRODUCTION CUT': 'OPEC',  # Contextual alias for OPEC
    'OIL OUTPUT CUT': 'OPEC',  # Contextual alias for OPEC
    'CRUDE OUTPUT': 'OPEC',  # Contextual alias for OPEC
    'JPMORGAN': 'JPM', 'GOLDMAN SACHS': 'GS', 'MORGAN STANLEY': 'MS',
    'BOEING': 'BA', 'LOCKHEED': 'LMT', 'RAYTHEON': 'RTX',
    'EXXON': 'XOM', 'CHEVRON': 'CVX', 'SHELL': 'SHEL',
    'PFIZER': 'PFE', 'MODERNA': 'MRNA', 'JOHNSON': 'JNJ',
    'WALMART': 'WMT', 'COSTCO': 'COST', 'DISNEY': 'DIS',
    'INTEL': 'INTC', 'AMD': 'AMD', 'QUALCOMM': 'QCOM',
    'MAERSK': 'MAERSK', 'EVERGREEN': 'EVERGREEN',  # Shipping
    'COINBASE': 'COIN', 'RIPPLE': 'XRP', 'SOLANA': 'SOL',
}

TICKERS = {
    # S&P 500 top 50 (3+ chars only)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'JPM',
    'UNH', 'JNJ', 'WMT', 'PEP', 'XOM', 'CVX', 'MRK', 'ABBV',
    'LLY', 'COST', 'AVGO', 'MCD', 'TMO', 'CSCO', 'ACN', 'ABT',
    'DHR', 'ADBE', 'CRM', 'NFLX', 'TXN', 'CMCSA', 'AMD', 'INTC', 'QCOM', 'INTU',
    'AMAT', 'PYPL', 'CAT', 'HON', 'IBM', 'AXP',
    # S&P 500 next 50 (3+ chars only)
    'ISRG', 'MDLZ', 'GILD', 'ADI', 'REGN', 'VRTX', 'BKNG', 'SYK', 'LRCX', 'PANW',
    'ADP', 'MMC', 'SBUX', 'KLAC', 'BSX', 'BMY', 'SCHW', 'TMUS',
    'SNPS', 'CDNS', 'CME', 'EOG', 'DUK', 'ICE',
    'SHW', 'MCK', 'PLD', 'NOC', 'USB', 'APD', 'TGT', 'MMM', 'SPGI',
    'FDX', 'CCI', 'EMR', 'BDX', 'ORLY', 'NSC', 'COF', 'FTNT', 'AJG', 'ADSK',
    # S&P 500 next 100 (3+ chars only)
    'ECL', 'SRE', 'AFL', 'JCI', 'HUM', 'PSA', 'TRV',
    'AEP', 'ROP', 'MPC', 'PSX', 'VLO', 'OXY', 'DVN', 'HAL', 'SLB', 'FANG',
    'PEG', 'EXC', 'AIG', 'MET', 'PRU', 'ALL', 'WELL',
    'SPG', 'DLR', 'EQIX', 'AMT', 'AVB', 'EQR', 'WEC', 'MSCI', 'FICO',
    'VRSK', 'CPRT', 'ODFL', 'FAST', 'PAYX', 'MCHP', 'NXPI', 'GWW', 'STZ',
    'KMB', 'HSY', 'GIS', 'SJM', 'HRL', 'MKC', 'CLX', 'CHD', 'MNST',
    'WBA', 'DXCM', 'IDXX', 'MTD', 'IQV', 'ZBH', 'BAX',
    'ALGN', 'HOLX', 'ZTS', 'TECH', 'PKI', 'ILMN', 'CTLT', 'CRL', 'WAT',
    'CARR', 'OTIS', 'LEN', 'DHI', 'PHM', 'NVR', 'LOW', 'POOL', 'WST', 'ROST',
    'TJX', 'DLTR', 'BBY', 'ULTA', 'NKE', 'LULU', 'TPR', 'HLT',
    # Previous extras not in S&P lists above
    'BAC', 'ORCL', 'DIS', 'PFE',
    # Major crypto
    'BTC', 'ETH', 'XRP', 'SOL', 'BNB', 'DOGE', 'ADA', 'AVAX', 'DOT', 'MATIC',
    'LINK', 'UNI',
    # Commodities
    'WTI', 'BRENT', 'GOLD', 'SILVER', 'COPPER', 'NATGAS', 'WHEAT', 'CORN', 'SOY',
    # Indices
    'SPX', 'SPY', 'NDX', 'QQQ', 'DJI', 'VIX', 'FTSE', 'DAX', 'NIKKEI', 'HSI',
    # Currencies
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCNY',
}

# ---------------------------------------------------------------------------
# CVE pattern
# ---------------------------------------------------------------------------
CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}')

# ---------------------------------------------------------------------------
# Country names -> ISO codes (top 50 by geopolitical relevance)
# ---------------------------------------------------------------------------
COUNTRY_MAP = {
    'United States': 'US', 'United Kingdom': 'GB', 'China': 'CN', 'Russia': 'RU',
    'Ukraine': 'UA', 'India': 'IN', 'Japan': 'JP', 'Germany': 'DE', 'France': 'FR',
    'Italy': 'IT', 'Canada': 'CA', 'Australia': 'AU', 'Brazil': 'BR', 'Mexico': 'MX',
    'South Korea': 'KR', 'North Korea': 'KP', 'Iran': 'IR', 'Iraq': 'IQ',
    'Israel': 'IL', 'Palestine': 'PS', 'Saudi Arabia': 'SA', 'Turkey': 'TR',
    'Egypt': 'EG', 'South Africa': 'ZA', 'Nigeria': 'NG', 'Kenya': 'KE',
    'Pakistan': 'PK', 'Afghanistan': 'AF', 'Indonesia': 'ID', 'Philippines': 'PH',
    'Vietnam': 'VN', 'Thailand': 'TH', 'Taiwan': 'TW', 'Singapore': 'SG',
    'Poland': 'PL', 'Netherlands': 'NL', 'Belgium': 'BE', 'Sweden': 'SE',
    'Norway': 'NO', 'Finland': 'FI', 'Denmark': 'DK', 'Switzerland': 'CH',
    'Spain': 'ES', 'Portugal': 'PT', 'Greece': 'GR', 'Argentina': 'AR',
    'Colombia': 'CO', 'Venezuela': 'VE', 'Cuba': 'CU', 'Jamaica': 'JM',
    'Trinidad': 'TT', 'Barbados': 'BB',
}

# ---------------------------------------------------------------------------
# Organizations (major international bodies, agencies, and tech companies)
# ---------------------------------------------------------------------------
ORGANIZATIONS = [
    'NATO', 'EU', 'UN', 'WHO', 'IMF', 'OPEC', 'OPEC+', 'FBI', 'CIA', 'NSA', 'CISA',
    'SEC', 'Fed', 'ECB', 'BOJ', 'PBOC', 'Maersk', 'Evergreen', 'Tesla', 'Apple',
    'Microsoft', 'Google', 'Amazon', 'Meta', 'NVIDIA', 'OpenAI', 'Anthropic',
    'IAEA', 'BRICS', 'ASEAN', 'OECD', 'WTO', 'ICC', 'Interpol',
    'Pentagon', 'Kremlin', 'Mossad', 'MI6', 'GCHQ',
    'Lockheed Martin', 'Raytheon', 'Boeing', 'Airbus',
    'Goldman Sachs', 'JPMorgan', 'Citibank', 'HSBC', 'Deutsche Bank',
]

# ---------------------------------------------------------------------------
# Supply Chain entities
# ---------------------------------------------------------------------------
SUPPLY_CHAIN_ENTITIES = {
    'ports': ['Port of Shanghai', 'Port of Singapore', 'Port of Rotterdam', 'Port of Los Angeles',
              'Port of Long Beach', 'Suez Canal', 'Panama Canal', 'Strait of Hormuz', 'Strait of Malacca',
              'Bab el-Mandeb', 'Cape of Good Hope'],
    'shipping_companies': ['Maersk', 'MSC', 'CMA CGM', 'COSCO', 'Hapag-Lloyd', 'ONE', 'Evergreen',
                           'Yang Ming', 'HMM', 'ZIM'],
    'commodities': ['crude oil', 'natural gas', 'LNG', 'wheat', 'corn', 'soybeans', 'lithium',
                    'cobalt', 'rare earth', 'copper', 'aluminum', 'steel', 'semiconductor', 'chips'],
}

# ---------------------------------------------------------------------------
# Humanitarian entities
# ---------------------------------------------------------------------------
HUMANITARIAN_ENTITIES = {
    'crises': ['famine', 'drought', 'flood', 'cyclone', 'typhoon', 'hurricane', 'earthquake',
               'tsunami', 'wildfire', 'epidemic', 'pandemic', 'cholera', 'ebola', 'displacement'],
    'organizations': ['UNHCR', 'UNICEF', 'WFP', 'ICRC', 'MSF', 'WHO', 'OCHA', 'IOM', 'UNDP',
                      'Red Cross', 'Red Crescent', 'Doctors Without Borders', 'Oxfam', 'Save the Children'],
    'frameworks': ['IPC', 'INFORM', 'GDACS', 'CERF', 'Flash Appeal', 'HRP', 'Cluster System'],
}

# ---------------------------------------------------------------------------
# MITRE ATT&CK keyword -> technique/tactic mapping (Cyber Pack)
# ---------------------------------------------------------------------------
MITRE_KEYWORDS = {
    'phishing': 'T1566', 'spearphishing': 'T1566.001', 'ransomware': 'T1486',
    'supply chain': 'T1195', 'zero-day': 'T1190', 'credential dumping': 'T1003',
    'lateral movement': 'TA0008', 'privilege escalation': 'TA0004',
    'command and control': 'TA0011', 'data exfiltration': 'TA0010',
    'brute force': 'T1110', 'DDoS': 'T1498', 'SQL injection': 'T1190',
    'watering hole': 'T1189', 'drive-by': 'T1189', 'keylogger': 'T1056',
    'rootkit': 'T1014', 'backdoor': 'T1059', 'botnet': 'T1583.005',
    'wiper': 'T1485', 'cryptominer': 'T1496',
}

# ---------------------------------------------------------------------------
# IOC regex patterns (Cyber Pack)
# ---------------------------------------------------------------------------
IOC_PATTERNS = {
    'ipv4': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    'md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
    'sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'domain': re.compile(
        r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:'
        r'ru|cn|tk|top|xyz|pw|cc|su|buzz|icu|club|work|gq|cf|ga|ml'
        r')\b'
    ),
}


def extract_mitre_tags(text):
    """Return list of matched MITRE ATT&CK technique IDs from *text*.

    Matching is case-insensitive. Each technique ID appears at most once.
    """
    text_lower = text.lower()
    seen = set()
    tags = []
    for keyword, technique in MITRE_KEYWORDS.items():
        if keyword.lower() in text_lower and technique not in seen:
            tags.append(technique)
            seen.add(technique)
    return tags


def extract_iocs(text):
    """Return dict of IOC types -> lists of matched indicators from *text*.

    Only keys with non-empty lists are included.
    """
    results = {}
    for ioc_type, pattern in IOC_PATTERNS.items():
        matches = list(set(pattern.findall(text)))
        if matches:
            # Basic validation for IPv4 — each octet must be 0-255
            if ioc_type == 'ipv4':
                valid = []
                for ip in matches:
                    octets = ip.split('.')
                    if all(0 <= int(o) <= 255 for o in octets):
                        valid.append(ip)
                matches = valid
            if matches:
                results[ioc_type] = sorted(matches)
    return results


def extract_supply_chain_entities(text):
    """Extract supply chain entities (ports, shipping companies, commodities) from *text*.

    Parameters
    ----------
    text : str
        Combined signal text to scan.

    Returns
    -------
    dict
        Only keys with non-empty lists are included. Possible keys:
        ``ports``, ``shipping_companies``, ``commodities``.
    """
    text_lower = text.lower()
    text_upper = text.upper()
    results = {}

    for category, terms in SUPPLY_CHAIN_ENTITIES.items():
        matched = []
        for term in terms:
            # Case-insensitive check
            if term.lower() in text_lower or term.upper() in text_upper:
                matched.append(term)
        if matched:
            results[category] = matched

    return results


def extract_humanitarian_entities(text):
    """Extract humanitarian entities (crises, organizations, frameworks) from *text*.

    Parameters
    ----------
    text : str
        Combined signal text to scan.

    Returns
    -------
    dict
        Only keys with non-empty lists are included. Possible keys:
        ``crises``, ``organizations``, ``frameworks``.
    """
    text_lower = text.lower()
    text_upper = text.upper()
    results = {}

    for category, terms in HUMANITARIAN_ENTITIES.items():
        matched = []
        for term in terms:
            if term.lower() in text_lower or term.upper() in text_upper:
                matched.append(term)
        if matched:
            results[category] = matched

    return results


def extract_entities(title, summary=''):
    """Extract financial tickers, CVEs, countries, organizations, MITRE ATT&CK tags, IOCs,
    supply chain entities, and humanitarian entities.

    Parameters
    ----------
    title : str
        Signal title.
    summary : str
        Signal summary (optional).

    Returns
    -------
    dict
        Only keys with non-empty lists/dicts are included. Possible keys:
        ``tickers``, ``cves``, ``countries``, ``organizations``,
        ``mitre_attack``, ``iocs``, ``supply_chain``, ``humanitarian``.
    """
    combined = (title or '') + ' ' + (summary or '')
    text_upper = combined.upper()

    entities = {
        'tickers': [],
        'cves': [],
        'countries': [],
        'organizations': [],
    }

    # Tickers (word-boundary match on uppercased text, skip stop words)
    matched_tickers = set()
    for ticker in TICKERS:
        if ticker.lower() in STOP_WORDS:
            continue
        if re.search(r'\b' + re.escape(ticker) + r'\b', text_upper):
            matched_tickers.add(ticker)

    # Also check ticker aliases (company names -> ticker symbols)
    for alias, ticker in TICKER_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_upper):
            matched_tickers.add(ticker)

    entities['tickers'] = sorted(matched_tickers)

    # CVEs (case-insensitive in original text)
    for m in CVE_PATTERN.finditer(combined):
        entities['cves'].append(m.group())

    # Organizations -- short names (<=4 chars) require case-sensitive match
    # to avoid false positives like "who" matching "WHO".
    seen_orgs = set()
    for org in ORGANIZATIONS:
        if len(org) <= 4:
            # Case-sensitive word-boundary match on original text
            matched = bool(re.search(r'\b' + re.escape(org) + r'\b', combined))
        else:
            matched = org.upper() in text_upper or org in combined
        if matched and org not in seen_orgs:
            entities['organizations'].append(org)
            seen_orgs.add(org)

    # Countries
    seen_countries = set()
    for name, code in COUNTRY_MAP.items():
        if name.upper() in text_upper:
            if code not in seen_countries:
                entities['countries'].append(code)
                seen_countries.add(code)

    # MITRE ATT&CK tagging (Cyber Pack)
    mitre_tags = extract_mitre_tags(combined)
    if mitre_tags:
        entities['mitre_attack'] = mitre_tags

    # IOC extraction (Cyber Pack)
    iocs = extract_iocs(combined)
    if iocs:
        entities['iocs'] = iocs

    # Supply Chain entity extraction
    sc_entities = extract_supply_chain_entities(combined)
    if sc_entities:
        entities['supply_chain'] = sc_entities

    # Humanitarian entity extraction
    hum_entities = extract_humanitarian_entities(combined)
    if hum_entities:
        entities['humanitarian'] = hum_entities

    # Return only non-empty keys
    return {k: v for k, v in entities.items() if v}
