# OracleFlow Phased Fix Plan -- Chief Architect Blueprint

**Date:** 2026-03-27
**Baseline:** 4.1/10 average across 5 customers (0 would pay today)
**Target:** 9-10/10 for all 5 customers, all eager to buy
**Constraints:** No Slack, dummy SMTP for email, no real Stripe, focus on value not infrastructure

---

## PHASE 1: Data Quality Decontamination
**Goal:** Fix the 7 universal issues that destroy trust for every customer
**Time:** 1 day (8 hours with 3 parallel agents)
**Parallel agents:** 3

### 1A -- Feed Pollution + Deduplication (Agent 1, ~4 hours)

**Problem:** Cyber category is 80% consumer tech (ZDNet general feed leaks gadget reviews). Supply chain has 3/4 aviation hobbyist feeds. Category filter leaks unrelated signals via `anomaly_score >= 0.8` passthrough. Dedup uses exact title match only.

**Fix 1: Remove ZDNet general feed pollution**
- **File:** `backend/app/oracleflow/feeds/global_feeds.py`
- **Action:** Line 49 -- the ZDNet feed URL `https://www.zdnet.com/topic/security/rss.xml` appears correct (it is the security-specific feed), but ZDNet's security RSS actually includes consumer tech. REPLACE with ZDNet's actual cybersecurity-only feed or remove entirely and add dedicated replacements:
  - Remove: `("https://www.zdnet.com/topic/security/rss.xml", "cyber", "ZDNet Security")`
  - Add: `("https://www.us-cert.gov/ncas/alerts.xml", "cyber", "US-CERT Alerts")`
  - Add: `("https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml", "cyber", "NVD CVE Feed")`
  - Add: `("https://otx.alienvault.com/api/v1/pulses/subscribed_pulse/feed", "cyber", "AlienVault OTX")`
  - Add: `("https://bazaar.abuse.ch/export/csv/recent/", "cyber", "MalwareBazaar")`
  - Add: `("https://www.microsoft.com/en-us/msrc/feed", "cyber", "Microsoft MSRC")`

**Fix 2: Replace aviation hobbyist supply chain feeds**
- **File:** `backend/app/oracleflow/feeds/global_feeds.py`
- **Action:** Lines 258-260 -- Remove `Simple Flying`, `Airline Geeks`, `AviationPros` from supply_chain category. Replace with real logistics feeds:
  - Remove the 3 aviation hobbyist feeds
  - Add: `("https://www.supplychaindive.com/feeds/news/", "supply_chain", "Supply Chain Dive")`
  - Add: `("https://www.joc.com/rss/all", "supply_chain", "JOC")`
  - Add: `("https://lloydslist.maritimeintelligence.informa.com/rss/news", "supply_chain", "Lloyds List")`
  - Add: `("https://www.hellenicshippingnews.com/feed/", "supply_chain", "Hellenic Shipping")`
  - Add: `("https://splash247.com/feed/", "supply_chain", "Splash247 Maritime")`
  - Add: `("https://www.seatrade-maritime.com/rss.xml", "supply_chain", "Seatrade Maritime")`
  - Add: `("https://theloadstar.com/feed/", "supply_chain", "The Loadstar")`
  - Add: `("https://www.porttechnology.org/feed/", "supply_chain", "Port Technology")`
  - Add: `("https://gcaptain.com/feed/", "supply_chain", "gCaptain")` (move from geopolitical -- this is a maritime/supply chain source)
  - Keep existing: `("https://www.freightwaves.com/news/feed", "supply_chain", "FreightWaves")`
  - Total: 10 supply chain feeds (was 4, 3 of which were wrong)

**Fix 3: Remove category filter pollution (anomaly passthrough)**
- **File:** `backend/app/oracleflow/api/signals.py`
- **Action:** Line 88 -- the category filter currently reads:
  ```python
  cat_filter = or_(Signal.category.in_(cat_list), Signal.anomaly_score >= 0.8)
  ```
  Change to strict category filtering:
  ```python
  cat_filter = Signal.category.in_(cat_list)
  ```
  This single line is why every customer sees unrelated content in their category view.

**Fix 4: Content-hash deduplication**
- **File:** `backend/app/oracleflow/feeds/rss.py`
- **Function:** `_is_duplicate()` (line 14)
- **Action:** Replace exact title match with a two-layer check:
  1. Exact title match (existing, fast path)
  2. Content hash: compute `hashlib.md5(normalized_title.encode()).hexdigest()` where `normalized_title` strips punctuation, lowercases, removes common prefixes like "Breaking:" -- store as `content_hash` field
  3. Fuzzy title match using `SequenceMatcher` with 0.85 threshold (import already available in `merger.py`)
- **Also modify:** `backend/app/oracleflow/models/signal.py` -- add `content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)` to Signal model

**Fix 5: Improve search from substring to word-boundary matching**
- **File:** `backend/app/oracleflow/api/signals.py`
- **Action:** Lines 97-99 -- the current `ILIKE %search%` causes "APT" to match "capture". Add word-boundary awareness:
  ```python
  keyword = f"% {search} %"  # space-padded for word boundaries
  keyword_start = f"{search} %"  # matches at start of field
  keyword_end = f"% {search}"  # matches at end
  search_filter = or_(
      Signal.title.ilike(f"% {search} %"),
      Signal.title.ilike(f"{search} %"),
      Signal.title.ilike(f"% {search}"),
      Signal.title == search,
      Signal.summary.ilike(f"% {search} %"),
      Signal.summary.ilike(f"{search} %"),
      Signal.summary.ilike(f"% {search}"),
  )
  ```

### 1B -- Sentiment Analysis + Country Expansion (Agent 2, ~6 hours)

**Fix 6: Working sentiment analysis**
- **File:** `backend/app/oracleflow/feeds/rss.py`
- **Function:** `fetch_global_feeds()` -- line 58, currently hardcodes `sentiment_score=0.0`
- **Action:** Implement keyword-based sentiment scoring (no external API needed):
  - Create new function `_compute_sentiment(text: str) -> float` in same file
  - Returns value from -1.0 (very negative) to +1.0 (very positive)
  - Positive keywords: "growth", "gains", "recovery", "peace", "agreement", "success", "profit", "surge", "breakthrough", "deal" (weight +0.15 each)
  - Negative keywords: "crisis", "crash", "war", "attack", "killed", "sanctions", "collapse", "threat", "recession", "plunge", "casualties", "conflict" (weight -0.15 each)
  - Neutral baseline: 0.0
  - Clamp to [-1.0, 1.0]
  - Replace `sentiment_score=0.0` with `sentiment_score=_compute_sentiment(title + " " + summary)`
- **Also fix in:** `backend/app/oracleflow/scheduler.py` lines 644-660 (the `_emit_signal_from_diff` fallback also hardcodes `sentiment_score=0.0`)

**Fix 7: Expand country registry from 5 to 50+ countries**
- **Directory:** `backend/app/oracleflow/registry/countries/`
- **Action:** Create 50 new YAML files following `_template.yaml` format. Priority countries:

  **Tier A (crisis/finance/geopolitical hotspots -- 20 countries):**
  china.yaml (CN), russia.yaml (RU), ukraine.yaml (UA), iran.yaml (IR), israel.yaml (IL), syria.yaml (SY), taiwan.yaml (TW), north_korea.yaml (KP), saudi_arabia.yaml (SA), turkey.yaml (TR), pakistan.yaml (PK), afghanistan.yaml (AF), myanmar.yaml (MM), sudan.yaml (SD), south_sudan.yaml (SS), yemen.yaml (YE), somalia.yaml (SO), drc.yaml (CD), venezuela.yaml (VE), nigeria.yaml (NG)

  **Tier B (major economies + political interest -- 15 countries):**
  germany.yaml (DE), france.yaml (FR), japan.yaml (JP), south_korea.yaml (KR), brazil.yaml (BR), mexico.yaml (MX), indonesia.yaml (ID), australia.yaml (AU), canada.yaml (CA), united_kingdom.yaml (GB), south_africa.yaml (ZA), egypt.yaml (EG), colombia.yaml (CO), argentina.yaml (AR), poland.yaml (PL)

  **Tier C (humanitarian + supply chain hubs -- 15 countries):**
  bangladesh.yaml (BD), ethiopia.yaml (ET), haiti.yaml (HT), mozambique.yaml (MZ), mali.yaml (ML), burkina_faso.yaml (BF), niger.yaml (NE), chad.yaml (TD), libya.yaml (LY), iraq.yaml (IQ), lebanon.yaml (LB), singapore.yaml (SG), netherlands.yaml (NL), panama.yaml (PA), uae.yaml (AE)

- Each YAML needs: country name, ISO code, region, languages, timezone, 3-5 news sources, 1-2 government sources, and key political entities

**Fix 8: Expand country guessing in RSS pipeline**
- **File:** `backend/app/oracleflow/feeds/rss.py`
- **Function:** `_guess_country()` (line 84) -- currently only 12 country hint sets
- **Action:** Expand to 55+ country hint sets matching all registry countries. Add keywords for leaders, capital cities, demonyms, and common abbreviations.

### 1C -- Chaos Index Fix + Displacement Data (Agent 3, ~3 hours)

**Fix 9: Include politics and crime in Chaos Index**
- **File:** `backend/app/oracleflow/pipeline/chaos.py`
- **Action:** Lines 20-26 -- `_CATEGORY_WEIGHTS` currently only includes finance, geopolitical, supply_chain, cyber, climate. For political intelligence customers, this is fundamentally broken.
- **Change to:**
  ```python
  _CATEGORY_WEIGHTS: dict[str, float] = {
      SignalCategory.FINANCE.value: 0.15,
      SignalCategory.GEOPOLITICAL.value: 0.20,
      SignalCategory.SUPPLY_CHAIN.value: 0.10,
      SignalCategory.CYBER.value: 0.10,
      SignalCategory.CLIMATE.value: 0.10,
      SignalCategory.POLITICS.value: 0.15,
      SignalCategory.CRIME.value: 0.10,
      SignalCategory.ECONOMY.value: 0.10,
  }
  ```
  Weights sum to 1.0. Politics+crime now 25% of the index.

**Fix 10: Mark displacement data as live-fetched or replace with real API**
- **File:** `backend/app/oracleflow/feeds/displacement.py`
- **Action:** Replace the static dict with a function that attempts to fetch from the UNHCR Population Statistics API (`https://api.unhcr.org/population/v1/`). On failure, fall back to the current static data but include a `"data_source": "cached_fallback", "last_updated": "2025-06-30"` field so the frontend can display a warning. Add `"data_source": "unhcr_api", "fetched_at": <timestamp>` on success.
- **Also modify frontend:** `frontend/src/components/panels/DisplacementPanel.vue` -- display the `data_source` field as a badge ("LIVE" vs "CACHED - Last updated: <date>")

### Phase 1 Score Impact Estimates

| Customer | Before | After Phase 1 | Delta | Reasoning |
|----------|--------|---------------|-------|-----------|
| Marcus (Hedge Fund) | 5.5 | 7.0 | +1.5 | Sentiment works (+1.0), dedup fixed (+0.25), country expansion (+0.25) |
| Sarah (Political) | 5.5 | 7.5 | +2.0 | 50 countries (+1.0), Chaos Index includes politics (+0.5), sentiment (+0.25), dedup (+0.25) |
| James (Supply Chain) | 4.0 | 6.0 | +2.0 | Real SC feeds (+1.5), dedup (+0.25), category filter fixed (+0.25) |
| Alex (Cyber) | 2.5 | 5.0 | +2.5 | ZDNet pollution gone (+1.5), search fixed (+0.5), dedup (+0.25), category filter (+0.25) |
| Maria (Humanitarian) | 3.0 | 5.0 | +2.0 | 50 countries (+1.0), displacement labeled/live (+0.5), sentiment (+0.25), dedup (+0.25) |

**New Average: 6.1/10 (from 4.1)**

---

## PHASE 2: Alert Delivery + Entity Extraction + Simulation Bridge
**Goal:** Connect the three disconnected pillars (alerts, entities, simulation)
**Time:** 3 days (with 3 parallel agents)
**Parallel agents:** 3

### 2A -- Email Alert Delivery Pipeline (Agent 1, ~2 days)

**Fix 11: Build email delivery backend**
- **New file:** `backend/app/oracleflow/alerts/delivery.py`
- **Action:** Create `AlertDeliveryService` class with methods:
  - `deliver_email(recipient_email, subject, body_html)` -- uses Python `smtplib` with configurable SMTP (default: localhost:1025 for testing with `aiosmtpd` or Python's `smtpd`)
  - `deliver_webhook(url, payload_json)` -- HTTP POST with retry (3 attempts)
  - `log_delivery(alert_id, channel, status, detail)` -- writes to a delivery log file at `backend/logs/alert_deliveries.log` as structured JSON lines
  - If SMTP fails, fall back to appending the full email (to, subject, body) to `backend/logs/email_outbox.log` -- this proves the email FLOW works end-to-end

- **Config additions to:** `backend/app/config.py`
  ```python
  SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
  SMTP_PORT = int(os.environ.get('SMTP_PORT', '1025'))
  SMTP_USER = os.environ.get('SMTP_USER', '')
  SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
  SMTP_FROM = os.environ.get('SMTP_FROM', 'alerts@oracleflow.io')
  SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'false').lower() == 'true'
  ALERT_EMAIL_LOG = os.environ.get('ALERT_EMAIL_LOG', os.path.join(os.path.dirname(__file__), '../logs/email_outbox.log'))
  ```

**Fix 12: Wire delivery into the scheduler pipeline**
- **File:** `backend/app/oracleflow/scheduler.py`
- **Function:** `_evaluate_alerts()` (line 197)
- **Action:** After creating an Alert record (line 249-256), call the delivery service:
  ```python
  from app.oracleflow.alerts.delivery import AlertDeliveryService
  delivery = AlertDeliveryService()
  # Look up user email from the alert rule's user_id
  for channel in rule.channels:
      if channel == "email":
          delivery.deliver_email(user_email, subject, body_html)
      elif channel == "webhook":
          delivery.deliver_webhook(rule.webhook_url, payload)
  ```
- Also add delivery for the `_create_fallback_alerts()` function

**Fix 13: Add user email field to auth model**
- **File:** `backend/app/oracleflow/auth/models.py`
- **Action:** Ensure `User` model has an `email` field (check if it exists -- if not, add `email: Mapped[str] = mapped_column(String(256), nullable=True)`)
- **File:** `backend/app/oracleflow/auth/routes.py`
- **Action:** Expose email in user preferences endpoint, allow updating notification email

**Fix 14: Frontend alert settings with email configuration**
- **File:** `frontend/src/views/SettingsView.vue`
- **Action:** Add "Alert Delivery" section with:
  - Email address input (pre-filled from user profile)
  - Toggle for email notifications (on/off)
  - Webhook URL input (optional)
  - Test button that triggers a test alert delivery
- **File:** `frontend/src/api/intelligence.js`
- **Action:** Add `testAlertDelivery` API call
- **File:** `backend/app/oracleflow/api/alerts.py`
- **Action:** Add `POST /api/alerts/test` endpoint that sends a test email

### 2B -- Entity Extraction on Signals (Agent 2, ~2 days)

**Fix 15: Run entity extraction on every new signal during ingest**
- **File:** `backend/app/oracleflow/feeds/rss.py`
- **Function:** `fetch_global_feeds()` -- after creating each Signal
- **Action:** Add lightweight regex-based entity extraction (NOT LLM-based, which is too slow for 200+ feeds):
  - Create new file: `backend/app/oracleflow/entities/signal_extractor.py`
  - Class `SignalEntityExtractor` with method `extract_from_signal(title, summary) -> dict` returning:
    ```python
    {
        "people": ["Name1", "Name2"],
        "organizations": ["Org1", "Org2"],
        "locations": ["Place1"],
        "tickers": ["AAPL", "MSFT"],  # regex: $[A-Z]{1,5} or standalone caps 1-5 chars
        "cve_ids": ["CVE-2026-12345"],  # regex: CVE-\d{4}-\d{4,}
        "ioc_indicators": [],  # IP addresses, domains, hashes
    }
    ```
  - Uses regex patterns:
    - People: sequences of 2-3 capitalized words (the existing `_CAPITALIZED_NAME_RE` from `extractor.py`)
    - Organizations: known org dictionary + capitalized multi-word with "Inc", "Corp", "Ltd", "Group"
    - Tickers: `\$[A-Z]{1,5}\b` or entries from a known ticker list
    - CVEs: `CVE-\d{4}-\d{4,}`
    - IOCs: IPv4 regex, MD5/SHA256 hash patterns, domain patterns
  - Store extracted entities in `Signal.raw_data_json["entities"]`

**Fix 16: Add entities field to signal API response**
- **File:** `backend/app/oracleflow/api/signals.py`
- **Function:** `list_signals()` -- line 149-162
- **Action:** Include entities from `raw_data_json.get("entities", {})` in the response:
  ```python
  entities = raw.get('entities', {})
  data.append({
      ...existing fields...,
      "entities": entities,
  })
  ```
- Add entity-based search: if `search` param matches a known entity name, include signals where `raw_data_json->entities` contains that name

**Fix 17: Frontend entity display on signal cards**
- **File:** `frontend/src/components/LiveFeed.vue`
- **Action:** In the signal card template, display entity chips:
  - Ticker chips (e.g., `$AAPL`) in blue
  - People chips in green
  - Organization chips in orange
  - CVE chips in red (for cyber users)
- **File:** `frontend/src/views/SignalsView.vue`
- **Action:** Add entity filter sidebar -- click on an entity name to filter signals by that entity

### 2C -- Simulation-Signal Bridge (Agent 3, ~2 days)

**Fix 18: "Simulate Impact" button on signal detail**
- **File:** `frontend/src/views/SignalsView.vue` or `frontend/src/components/LiveFeed.vue`
- **Action:** Add a "Simulate Impact" button on each signal card that:
  1. Opens a modal pre-filled with signal context
  2. Shows scenario template based on signal category:
     - Finance: "If [signal event] continues, impact on [asset/sector]?"
     - Geopolitical: "If [signal event] escalates, impact on [region/alliance]?"
     - Supply Chain: "If [signal event], cascading impact on [supply routes]?"
     - Cyber: "If [signal event] is exploited, impact on [sector/infrastructure]?"
  3. Submits to simulation API with signal_id reference

**Fix 19: Scenario simulation API bridge**
- **File:** `backend/app/api/simulation.py`
- **Action:** Add endpoint `POST /api/simulation/scenario` that:
  1. Accepts `signal_id` and optional `scenario_override` text
  2. Loads the signal and its entities
  3. Generates a scenario prompt using signal context + entities
  4. Runs the scenario through the LLM (using existing `LLMClient`) to produce:
     - Impact assessment (which sectors/entities are affected)
     - Probability estimate (low/medium/high)
     - Timeline (immediate/days/weeks/months)
     - Cascading effects list
  5. Returns structured JSON response
  6. Stores result in Simulation table with `signal_ids_json = [signal_id]`

**Fix 20: Frontend scenario results display**
- **File:** `frontend/src/views/SimulationRunView.vue`
- **Action:** Add a "Scenario Analysis" mode alongside the existing OASIS social simulation:
  - Shows the signal that triggered the scenario
  - Displays impact assessment as a card grid
  - Shows cascading effects as a flow diagram
  - Timeline visualization

### Phase 2 Score Impact Estimates

| Customer | Before | After Phase 2 | Delta | Reasoning |
|----------|--------|---------------|-------|-----------|
| Marcus (Hedge Fund) | 7.0 | 8.5 | +1.5 | Entity/ticker extraction (+0.5), scenario simulation (+0.5), email alerts (+0.5) |
| Sarah (Political) | 7.5 | 9.0 | +1.5 | Entity tracking across signals (+0.5), scenario sim (+0.5), email alerts (+0.5) |
| James (Supply Chain) | 6.0 | 8.0 | +2.0 | Email/webhook alerts (+1.5), entity extraction (+0.25), simulation bridge (+0.25) |
| Alex (Cyber) | 5.0 | 7.0 | +2.0 | CVE/IOC extraction (+1.0), entity extraction (+0.5), email alerts (+0.5) |
| Maria (Humanitarian) | 5.0 | 7.0 | +2.0 | Email alerts for early warning (+1.5), entity tracking (+0.25), simulation (+0.25) |

**New Average: 7.9/10 (from 6.1)**

---

## PHASE 3: Domain-Specific Depth Packs
**Goal:** Give each customer vertical-specific features that make OracleFlow irreplaceable
**Time:** 4 days (with 4 parallel agents)
**Parallel agents:** 4

### 3A -- Financial Intelligence Pack (Agent 1, ~3 days)
*Target: Marcus Chen -- Hedge Fund*

**Fix 21: Ticker extraction and financial entity enrichment**
- **File:** `backend/app/oracleflow/entities/signal_extractor.py` (created in Phase 2)
- **Action:** Add comprehensive financial entity extraction:
  - Maintain a list of top 500 tickers (S&P 500) for matching
  - Extract commodity references (WTI, Brent, Gold, Silver, Copper)
  - Extract index references (S&P 500, NASDAQ, Dow, VIX, FTSE, DAX, Nikkei)
  - Extract currency pairs (EUR/USD, etc.)
  - Store in `signal.raw_data_json["entities"]["tickers"]`

**Fix 22: Financial scenario simulation templates**
- **File:** `backend/app/api/simulation.py` (the scenario endpoint from Phase 2)
- **Action:** Add finance-specific scenario templates:
  - "Strait of Hormuz closure" -> impact on WTI, shipping stocks, VIX
  - "Fed rate decision" -> impact on USD, bonds, equities
  - "China-Taiwan escalation" -> impact on semiconductors, TSMC, supply chains
  - Template structure: input signal -> affected tickers -> magnitude estimate -> timeline

**Fix 23: Diff engine latency proof**
- **File:** `backend/app/oracleflow/api/sites.py`
- **Action:** Add endpoint `GET /api/sites/<id>/latency` that returns:
  - Average detection latency (time between page change and signal creation)
  - Fastest detection time
  - Comparison benchmark: "Detection within X seconds of change"
- **Frontend:** `frontend/src/views/SiteDetailView.vue` -- display latency metrics

**Fix 24: Add SEC EDGAR and central bank feeds**
- **File:** `backend/app/oracleflow/feeds/global_feeds.py`
- **Action:** Add financial data feeds:
  - `("https://efts.sec.gov/LATEST/search-index?q=8-K&dateRange=custom&startdt=2026-03-20&enddt=2026-03-27&forms=8-K", "finance", "SEC EDGAR 8-K")`
  - `("https://www.ecb.europa.eu/rss/press.html", "finance", "ECB Press")`
  - `("https://www.bankofengland.co.uk/rss/news", "finance", "Bank of England")`
  - `("https://www.boj.or.jp/en/rss/whatsnew.xml", "finance", "Bank of Japan")`

### 3B -- Cyber Threat Intelligence Pack (Agent 2, ~3 days)
*Target: Alex Kim -- Cybersecurity*

**Fix 25: Structured threat data on cyber signals**
- **File:** `backend/app/oracleflow/entities/signal_extractor.py`
- **Action:** Add cyber-specific extraction:
  - CVE IDs with links to NVD (`https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX`)
  - CVSS score lookup (cache NVD API responses)
  - IOC patterns: IPv4, IPv6, domains, MD5, SHA1, SHA256, email addresses
  - MITRE ATT&CK technique IDs: `T\d{4}(\.\d{3})?`

**Fix 26: Add vendor security advisory feeds**
- **File:** `backend/app/oracleflow/feeds/global_feeds.py`
- **Action:** Add 15+ vendor advisory feeds:
  - `("https://api.msrc.microsoft.com/update-guide/rss", "cyber", "Microsoft MSRC")`
  - `("https://tools.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml", "cyber", "Cisco PSIRT")`
  - `("https://www.oracle.com/security-alerts/cpujan2026.html", "cyber", "Oracle Security")`
  - `("https://chromereleases.googleblog.com/feeds/posts/default", "cyber", "Chrome Releases")`
  - `("https://www.mozilla.org/en-US/security/advisories/feed/", "cyber", "Mozilla Security")`
  - `("https://access.redhat.com/blogs/product-security/feed", "cyber", "Red Hat Security")`
  - `("https://ubuntu.com/security/notices/rss.xml", "cyber", "Ubuntu Security")`
  - `("https://www.vmware.com/security/advisories.xml", "cyber", "VMware Security")`
  - `("https://www.fortiguard.com/rss/ir.xml", "cyber", "FortiGuard")`
  - `("https://www.paloaltonetworks.com/blog/feed", "cyber", "Palo Alto Networks")`
  - `("https://blog.talosintelligence.com/feeds/posts/default?alt=rss", "cyber", "Cisco Talos")`
  - `("https://unit42.paloaltonetworks.com/feed/", "cyber", "Unit 42")`
  - `("https://www.mandiant.com/resources/blog/rss.xml", "cyber", "Mandiant")`
  - `("https://securelist.com/feed/", "cyber", "Kaspersky Securelist")`

**Fix 27: Cyber-specific frontend panel**
- **File:** `frontend/src/components/panels/CyberPanel.vue`
- **Action:** Enhance to display:
  - CVE severity badges (Critical/High/Medium/Low based on CVSS)
  - IOC count per signal
  - MITRE ATT&CK technique tags
  - Threat actor labels (extracted entities of type "organization" in cyber category)

### 3C -- Humanitarian/NGO Pack (Agent 3, ~3 days)
*Target: Maria Santos -- NGO*

**Fix 28: GDACS integration**
- **New file:** `backend/app/oracleflow/feeds/gdacs.py`
- **Action:** Create GDACS feed fetcher:
  - RSS feed: `https://www.gdacs.org/xml/rss.xml` (all hazards)
  - Parse GDACS-specific fields: alert level (Red/Orange/Green), hazard type (EQ/TC/FL/VO/DR), affected population
  - Create signals with category "climate", enriched `raw_data_json`:
    ```python
    {
        "gdacs_alert_level": "Red",
        "gdacs_event_type": "earthquake",
        "magnitude": 7.2,
        "affected_population": 2500000,
        "gdacs_url": "https://www.gdacs.org/report.aspx?eventid=...",
    }
    ```
- **Wire into scheduler:** `backend/app/oracleflow/scheduler.py` `_fetch_feeds()` -- add `from app.oracleflow.feeds.gdacs import fetch_gdacs_alerts` and call it alongside USGS/ACLED/NASA

**Fix 29: Live displacement data from UNHCR API**
- **File:** `backend/app/oracleflow/feeds/displacement.py`
- **Action:** Replace the entire static dict with a proper fetcher:
  ```python
  import requests
  from datetime import datetime, timezone

  UNHCR_API = "https://api.unhcr.org/population/v1/"
  CACHE_TTL = 3600  # refresh hourly

  _cache = {"data": None, "fetched_at": None}

  def get_displacement_data():
      now = datetime.now(timezone.utc)
      if _cache["data"] and _cache["fetched_at"] and (now - _cache["fetched_at"]).seconds < CACHE_TTL:
          return {**_cache["data"], "data_source": "unhcr_api", "fetched_at": _cache["fetched_at"].isoformat()}
      try:
          resp = requests.get(f"{UNHCR_API}?limit=20&year=2025", timeout=10)
          resp.raise_for_status()
          # Parse UNHCR response into our format
          data = _parse_unhcr_response(resp.json())
          _cache["data"] = data
          _cache["fetched_at"] = now
          return {**data, "data_source": "unhcr_api", "fetched_at": now.isoformat()}
      except Exception:
          return {**STATIC_FALLBACK, "data_source": "cached_fallback", "last_updated": "2025-06-30"}
  ```

**Fix 30: Add IPC food security + INFORM Risk feeds**
- **File:** `backend/app/oracleflow/feeds/global_feeds.py`
- **Action:** Add humanitarian feeds:
  - `("https://reliefweb.int/updates/rss.xml", "climate", "ReliefWeb")`
  - `("https://www.ipcinfo.org/rss/en/", "climate", "IPC Food Security")`
  - `("https://www.fews.net/rss.xml", "climate", "FEWS NET")`
  - `("https://dtm.iom.int/rss", "climate", "IOM DTM")`
  - `("https://www.acaps.org/rss.xml", "climate", "ACAPS")`

### 3D -- Supply Chain + Political Depth (Agent 4, ~3 days)
*Target: James Rodriguez + Dr. Sarah Okafor*

**Fix 31: Cascading impact simulation for supply chain**
- **File:** `backend/app/api/simulation.py` (extending scenario endpoint)
- **Action:** Add supply chain scenario template:
  - Input: signal about port closure / natural disaster / sanctions
  - LLM prompt generates: affected shipping routes, alternative routes, estimated delay days, affected commodities
  - Output structure:
    ```json
    {
        "trigger": "Port of Rotterdam congestion",
        "affected_routes": ["Asia-Europe", "Transatlantic"],
        "cascading_effects": [
            {"entity": "European auto manufacturers", "impact": "3-5 day delay", "severity": "high"},
            {"entity": "Chemical supply chain", "impact": "Price spike 8-12%", "severity": "medium"}
        ],
        "alternative_routes": ["Port of Antwerp", "Port of Hamburg"],
        "estimated_timeline": "2-3 weeks"
    }
    ```

**Fix 32: Country risk trend lines (time series)**
- **File:** `backend/app/oracleflow/api/countries.py`
- **Action:** Add endpoint `GET /api/countries/<code>/risk-history?days=30` that:
  - Queries ChaosIndex snapshots filtered by signals from that country
  - Returns daily aggregated scores as time series
  - Includes per-category breakdown over time
- **Frontend:** `frontend/src/views/CountryDetailView.vue` -- add Chart.js line chart showing risk trend

**Fix 33: Political entity tracking dashboard**
- **File:** `frontend/src/views/EntitiesView.vue`
- **Action:** Add "Track Entity" feature:
  - User can pin entities (leaders, organizations, parties)
  - Dashboard shows all signals mentioning pinned entities
  - Timeline of entity mentions (frequency chart)
- **Backend:** `backend/app/oracleflow/api/entities.py`
- **Action:** Add `GET /api/entities/<id>/signals` endpoint that queries signals containing the entity name in `raw_data_json->entities`

### Phase 3 Score Impact Estimates

| Customer | Before | After Phase 3 | Delta | Reasoning |
|----------|--------|---------------|-------|-----------|
| Marcus (Hedge Fund) | 8.5 | 9.5 | +1.0 | Ticker extraction depth (+0.5), financial sim templates (+0.25), SEC feeds (+0.25) |
| Sarah (Political) | 9.0 | 9.5 | +0.5 | Country risk trends (+0.25), entity tracking dashboard (+0.25) |
| James (Supply Chain) | 8.0 | 9.5 | +1.5 | Cascading sim (+0.5), maritime feeds enrichment (+0.5), entity tracking (+0.5) |
| Alex (Cyber) | 7.0 | 9.5 | +2.5 | CVE/IOC data (+1.0), vendor advisories (+0.5), MITRE ATT&CK (+0.5), clean feeds (+0.5) |
| Maria (Humanitarian) | 7.0 | 9.5 | +2.5 | GDACS (+1.0), live displacement (+0.5), IPC/FEWS feeds (+0.5), entity tracking (+0.5) |

**New Average: 9.5/10 (from 7.9)**

---

## PHASE 4: Polish, Proof Points, and Purchase Confidence
**Goal:** Close the last 0.5-1.0 points for each customer. Make them WANT to pay.
**Time:** 2 days (with 2 parallel agents)
**Parallel agents:** 2

### 4A -- Performance Proof + Plan Value (Agent 1, ~2 days)

**Fix 34: Diff engine latency dashboard**
- **File:** `frontend/src/views/DashboardView.vue`
- **Action:** Add "Detection Speed" widget showing:
  - Average page change detection time
  - Fastest detection this week
  - Comparison: "OracleFlow detected this Fed page change in 4m 32s"
  - Feed health with per-source signal counts

**Fix 35: Plan enforcement server-side**
- **File:** `backend/app/oracleflow/billing/enforcement.py`
- **Action:** Enforce category limits per plan:
  - Free: 3 categories
  - Scout ($49): 5 categories
  - Strategist ($199): All categories
  - Commander ($999): All + priority refresh
  - Sovereign ($5K): All + custom feeds + dedicated support
- Wire enforcement into signals API to filter categories by plan

**Fix 36: Demo mode with pre-loaded data per persona**
- **File:** `backend/app/oracleflow/auth/personas.py`
- **Action:** Ensure each demo persona gets a pre-seeded experience:
  - Hedge fund persona: pre-loaded with financial signals + ticker entities + scenario sim results
  - Political persona: pre-loaded with 10 country risk profiles + entity network + chaos history
  - Supply chain persona: pre-loaded with maritime signals + cascading sim example
  - Cyber persona: pre-loaded with CVE signals + IOC extracts + clean feed
  - Humanitarian persona: pre-loaded with GDACS alerts + displacement data + country crisis profiles

### 4B -- Frontend UX Polish (Agent 2, ~2 days)

**Fix 37: Signal card redesign with entity chips and sentiment bar**
- **File:** `frontend/src/components/LiveFeed.vue`
- **Action:** Each signal card now shows:
  - Sentiment bar (red-to-green gradient, not just 0.0)
  - Entity chips (clickable, filters to that entity)
  - Category badge
  - Source attribution
  - "Simulate Impact" quick action

**Fix 38: Notification panel shows delivery status**
- **File:** `frontend/src/components/NotificationPanel.vue`
- **Action:** Add delivery status indicators:
  - "Sent via email" badge
  - "Sent via webhook" badge
  - "In-app only" badge
  - Timestamp of delivery

**Fix 39: Onboarding flow per vertical**
- **File:** `frontend/src/components/OnboardingGuide.vue`
- **Action:** After persona selection, show a 3-step guided tour:
  1. "Your feeds are configured for [vertical]" -- show feed count and categories
  2. "Set up alerts" -- pre-fill alert rules for their vertical
  3. "Try a simulation" -- pre-fill a scenario relevant to their industry

### Phase 4 Score Impact Estimates

| Customer | Before | After Phase 4 | Delta | Reasoning |
|----------|--------|---------------|-------|-----------|
| Marcus (Hedge Fund) | 9.5 | 10 | +0.5 | Latency proof (+0.25), plan value clarity (+0.25) |
| Sarah (Political) | 9.5 | 10 | +0.5 | Onboarding (+0.25), UX polish (+0.25) |
| James (Supply Chain) | 9.5 | 10 | +0.5 | Enterprise polish (+0.25), notification delivery status (+0.25) |
| Alex (Cyber) | 9.5 | 10 | +0.5 | Clean UX (+0.25), onboarding (+0.25) |
| Maria (Humanitarian) | 9.5 | 10 | +0.5 | Onboarding for NGO (+0.25), sentiment visibility (+0.25) |

**Final Average: 10/10**

---

## COMPLETE FILE MANIFEST

### Backend Files Modified (existing)
| # | File | Phases | Changes |
|---|------|--------|---------|
| 1 | `backend/app/oracleflow/feeds/global_feeds.py` | 1, 3 | Remove polluted feeds, add 40+ domain-specific feeds |
| 2 | `backend/app/oracleflow/api/signals.py` | 1, 2 | Fix category filter, fix search, add entity field to response |
| 3 | `backend/app/oracleflow/feeds/rss.py` | 1, 2 | Content-hash dedup, sentiment scoring, entity extraction hook |
| 4 | `backend/app/oracleflow/pipeline/chaos.py` | 1 | Add politics+crime+economy to category weights |
| 5 | `backend/app/oracleflow/feeds/displacement.py` | 1, 3 | Replace static data with UNHCR API + fallback |
| 6 | `backend/app/oracleflow/models/signal.py` | 1 | Add content_hash column |
| 7 | `backend/app/oracleflow/scheduler.py` | 2, 3 | Wire alert delivery, add GDACS fetch, sentiment on diff signals |
| 8 | `backend/app/oracleflow/api/alerts.py` | 2 | Add test delivery endpoint |
| 9 | `backend/app/config.py` | 2 | Add SMTP config vars |
| 10 | `backend/app/oracleflow/auth/models.py` | 2 | Verify/add email field on User |
| 11 | `backend/app/oracleflow/auth/routes.py` | 2 | Expose email in preferences |
| 12 | `backend/app/api/simulation.py` | 2, 3 | Add scenario analysis endpoint |
| 13 | `backend/app/oracleflow/api/entities.py` | 3 | Add entity-signals endpoint |
| 14 | `backend/app/oracleflow/api/countries.py` | 3 | Add risk-history trend endpoint |
| 15 | `backend/app/oracleflow/billing/enforcement.py` | 4 | Server-side plan enforcement |
| 16 | `backend/app/oracleflow/auth/personas.py` | 4 | Pre-seeded demo data per persona |
| 17 | `backend/app/oracleflow/pipeline/merger.py` | 1 | Already has fuzzy matching (verify threshold) |

### Backend Files Created (new)
| # | File | Phase | Purpose |
|---|------|-------|---------|
| 1 | `backend/app/oracleflow/alerts/delivery.py` | 2 | Email + webhook delivery service |
| 2 | `backend/app/oracleflow/entities/signal_extractor.py` | 2 | Regex-based entity extraction for signals |
| 3 | `backend/app/oracleflow/feeds/gdacs.py` | 3 | GDACS natural disaster feed fetcher |
| 4 | 50 YAML files in `backend/app/oracleflow/registry/countries/` | 1 | Country configurations |

### Frontend Files Modified (existing)
| # | File | Phases | Changes |
|---|------|--------|---------|
| 1 | `frontend/src/components/LiveFeed.vue` | 2, 4 | Entity chips, sentiment bar, simulate button |
| 2 | `frontend/src/components/NotificationPanel.vue` | 4 | Delivery status badges |
| 3 | `frontend/src/components/panels/DisplacementPanel.vue` | 1 | Data source badge (LIVE vs CACHED) |
| 4 | `frontend/src/components/panels/CyberPanel.vue` | 3 | CVE/IOC/MITRE display |
| 5 | `frontend/src/views/SettingsView.vue` | 2 | Alert delivery configuration |
| 6 | `frontend/src/views/SignalsView.vue` | 2 | Entity filter sidebar |
| 7 | `frontend/src/views/SimulationRunView.vue` | 2 | Scenario analysis mode |
| 8 | `frontend/src/views/EntitiesView.vue` | 3 | Entity tracking dashboard |
| 9 | `frontend/src/views/CountryDetailView.vue` | 3 | Risk trend chart |
| 10 | `frontend/src/views/DashboardView.vue` | 4 | Detection speed widget |
| 11 | `frontend/src/views/SiteDetailView.vue` | 3 | Latency metrics |
| 12 | `frontend/src/components/OnboardingGuide.vue` | 4 | Vertical-specific onboarding |
| 13 | `frontend/src/api/intelligence.js` | 2, 3 | New API calls for delivery test, entity signals, risk history |

---

## RESOURCE SUMMARY

| Phase | Duration | Agents | Key Outcome |
|-------|----------|--------|-------------|
| **Phase 1** | 1 day | 3 | Data quality: avg 4.1 -> 6.1 |
| **Phase 2** | 3 days | 3 | Connectivity: avg 6.1 -> 7.9 |
| **Phase 3** | 4 days | 4 | Domain depth: avg 7.9 -> 9.5 |
| **Phase 4** | 2 days | 2 | Polish: avg 9.5 -> 10.0 |
| **TOTAL** | **10 days** | **4 max** | **4.1/10 -> 10/10, $7,246/mo revenue** |

---

## CRITICAL PATH

The single most important action is **Phase 1, Fix 3** -- removing the one line that causes category pollution:
```python
# FROM:
cat_filter = or_(Signal.category.in_(cat_list), Signal.anomaly_score >= 0.8)
# TO:
cat_filter = Signal.category.in_(cat_list)
```
This one line change impacts ALL 5 customers and takes 30 seconds to implement. It should be deployed immediately.
