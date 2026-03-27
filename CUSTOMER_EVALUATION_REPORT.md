# OracleFlow — Customer Evaluation Report

**Date:** 2026-03-27
**Method:** 5 real customer personas tested the live system via API + UI
**Scope:** Full flow from landing page to simulation, all features tested

---

## SCORES SUMMARY

| # | Customer | Industry | Score | Would Pay? | Target Plan |
|---|----------|----------|-------|------------|-------------|
| 1 | Marcus Chen | Hedge Fund ($2B AUM) | **5.5/10** | Not today. Maybe in 6 months | Commander $999/mo |
| 2 | Dr. Sarah Okafor | Political Intelligence | **5.5/10** | No | Sovereign $5,000/mo |
| 3 | James Rodriguez | Supply Chain Risk (F500) | **4/10** | No | Commander $999/mo |
| 4 | Alex Kim | Cybersecurity | **2.5/10** | No | Strategist $199/mo |
| 5 | Maria Santos | Humanitarian/NGO | **3/10** | No | Free / Scout $49/mo |

**Average Score: 4.1 / 10**

---

## WHAT EVERY CUSTOMER AGREED ON (Universal Issues)

### 1. Simulation is disconnected from intelligence
All 5 customers expected to click "Simulate Impact" on a signal and get a prediction. None could. The simulation engine exists but is designed for social media simulation (MiroFish's OASIS), not scenario analysis for their industry.

### 2. No real-time alerting
Every customer asked "how will I be notified?" The notification system stores alerts in a database but has NO push delivery — no email, no Slack, no webhook, no SMS. For an intelligence platform, this is a dealbreaker.

### 3. Duplicate signals
3 of 5 customers flagged the same articles appearing 2-5 times in their feed. The dedup uses exact title match but identical articles from different RSS feeds with slightly different titles slip through.

### 4. Category pollution
The `supply_chain` category contains aviation hobbyist articles. The `cyber` category contains Amazon deals and robot lawnmower reviews (from ZDNet's general feed). The critical signal passthrough (anomaly >= 0.8) leaks unrelated high-anomaly signals into every category filter.

### 5. Only 5 countries configured
The country registry has Jamaica, Trinidad, Barbados, India, USA. No Bangladesh, China, Russia, Iran, Syria, Sudan, or any of the 40+ countries customers actually care about.

### 6. Sentiment analysis is broken
All sentiment scores return 0.0. For the hedge fund analyst, sentiment IS the product. For every customer, it's a missing dimension.

### 7. No entity extraction
Signals have titles and categories but no extracted entities (people, organizations, tickers, locations). Nobody can search "show me all signals about Maersk" or "track regime change in Myanmar."

---

## PER-CUSTOMER DETAILED FINDINGS

---

### Customer 1: Marcus Chen — Hedge Fund Analyst
**Score: 5.5/10**

**What worked:**
- 434 signals in finance/economy/geopolitical categories — real, current, relevant
- Chaos Index is a novel regime detection indicator (geopolitical at 100.0 during Iran crisis = correct)
- Site monitoring diff engine on Fed/SEC websites = genuine alpha source
- AI intelligence briefs = unique vs Bloomberg
- Feed health transparency (214 feeds, 1,679 signals/24h)

**Why not 10/10:**
- -1.0: Sentiment analysis broken (all 0.0)
- -1.0: No ticker/symbol extraction (can't query "signals affecting AAPL")
- -0.5: Anomaly scoring doesn't differentiate market-moving vs routine news
- -0.5: No financial scenario simulation
- -0.5: Plan enforcement is leaky (categories not enforced server-side)
- -0.5: No latency benchmarks vs Bloomberg
- -0.5: No SEC EDGAR integration, no central bank data feeds

**Would pay $999/mo if:**
1. Working sentiment analysis with market impact scoring
2. Financial entity extraction (tickers, commodities, indices)
3. Proven sub-minute detection on Fed/SEC page changes
4. Financial scenario simulation ("If Iran closes Hormuz → impact on WTI, shipping stocks, VIX")
5. WebSocket/SSE push for real-time signals
6. SEC EDGAR 13F/8K monitoring as first-class signals

**Comparison:** Does NOT replace Bloomberg ($24K/yr) or Refinitiv ($15K/yr). Could supplement as early warning layer if diff engine proves faster.

---

### Customer 2: Dr. Sarah Okafor — Political Intelligence Consultant
**Score: 5.5/10**

**What worked:**
- 214 RSS feeds include top think tanks (CFR, CSIS, Brookings, Crisis Group, Chatham House, Carnegie, RAND, IISS) — better than manual monitoring
- Cross-source anomaly confirmation is genuinely useful for intelligence
- Diff engine architecture for government website monitoring is production-grade
- Political persona defaults are well-chosen
- ACLED conflict integration exists (if API key is configured)

**Why not 10/10:**
- -1.5: Only 5 countries configured (need 50+)
- -1.0: Chaos Index excludes politics and crime categories — fundamental flaw for political users
- -0.5: No scenario simulation for geopolitical "what-if" analysis
- -0.5: No entity extraction (can't track specific leaders, parties, organizations)
- -0.5: No historical trend analysis (country risk is point-in-time, not time series)
- -0.5: No election calendar, sanctions database, or treaty tracking
- -0.5: No collaborative intelligence (team annotation, shared assessments)
- -0.5: Country code guessing uses keyword matching with only 11 countries

**Would pay $5,000/mo if:**
1. 50+ country configs with government source URLs
2. Politics/crime weighted in Chaos Index (or separate Political Instability Index)
3. Entity extraction (NER) — track leaders, parties, militias across all signals
4. Per-country risk trend lines over time
5. Scenario simulation for geopolitical what-ifs
6. ACLED integration with real API key (not placeholders)
7. 25+ monitored government portals on Strategist plan

**Comparison:** Does NOT replace Stratfor ($40K/yr) or ACLED ($5K/yr). The 214-feed aggregation is better than manual monitoring but lacks analyst depth.

---

### Customer 3: James Rodriguez — VP Global Risk, Fortune 500
**Score: 4/10**

**What worked:**
- Architecture is well-structured with proper auth/billing scaffolding
- Geopolitical feed IS useful — gCaptain, think tanks, Reuters
- Diff engine with significance scoring is technically capable
- Alert rules support webhooks (infrastructure exists even if delivery doesn't)

**Why not 10/10:**
- -2.0: Supply chain category has 4 feeds out of 214 (1.8%) — critically underserved. 3 of 4 are aviation hobbyist sites, not logistics
- -1.5: No real-time alerting delivery (email, Slack, webhook, SMS)
- -0.5: Commander plan caps at 25 sites (need 50+ for supplier monitoring)
- -0.5: No maritime data (AIS, port congestion, container rates)
- -0.5: Simulation not integrated with intelligence layer
- -0.5: No enterprise features (SSO/SAML, audit logging, SLA)
- -0.5: Signal duplicates inflate feed

**Would pay $999/mo if:**
1. 20-30 dedicated supply chain feeds (Lloyd's List, FreightWaves, JOC, Drewry, Supply Chain Dive)
2. Maritime data (MarineTraffic AIS, port congestion APIs, WCI container rates)
3. Actual webhook/Slack/email delivery with <5 min SLA
4. Cascading impact simulation ("This port closed → your 12 suppliers affected → 3 alternative routes")
5. Supply chain entity extraction (recognize "Maersk", "Port of Rotterdam")
6. Sub-categories: supply_chain.maritime, supply_chain.air, supply_chain.semiconductors
7. SSO/SAML and audit logging for enterprise compliance

**Comparison:** Does NOT compete with Dataminr (real-time social), Everbridge (alerting), or current $200K/yr stack. Would evaluate as $49-199/mo supplementary geopolitical news tool.

---

### Customer 4: Alex Kim — Cybersecurity Threat Analyst
**Score: 2.5/10**

**What worked:**
- Feed list includes legitimate cyber sources (Krebs, Dark Reading, BleepingComputer, CyberScoop, The Record, CISA, Schneier)
- Some malware signals were relevant (CISA RESURGE analysis, LiteLLM supply chain attack)
- Architecture/infrastructure is solid

**Why not 10/10:**
- -3.0: "Cyber" category is catastrophically polluted — ZDNet's general feed puts Amazon deals, robot lawnmowers, and iPad reviews into cyber. ~80% of cyber signals are NOT cybersecurity
- -2.0: No structured threat data (no IOCs, CVE IDs, CVSS scores, STIX/TAXII)
- -1.0: No dark web, APT tracking, or threat actor database
- -0.5: Search for "APT" returns cricket articles (substring match on "capture")
- -0.5: Simulation engine is social media modeling, not cyber attack modeling
- -0.5: No MITRE ATT&CK integration

**Would pay $199/mo if:**
1. Fix ZDNet feed — separate actual security content from consumer tech
2. Add NVD/NIST CVE database API with CVSS scores
3. Add IOC feeds (AlienVault OTX, Abuse.ch, MalwareBazaar)
4. Add 20+ vendor security advisory feeds (Microsoft MSRC, Cisco PSIRT, etc.)
5. MITRE ATT&CK mapping on threat signals
6. Proper full-text search (not substring matching)
7. Deduplication that actually works

**Comparison:** Does NOT compete with Recorded Future ($50K/yr) or Mandiant ($30K/yr). Different product category entirely. This is a news aggregator, not a threat intelligence platform.

---

### Customer 5: Maria Santos — NGO Crisis Director
**Score: 3/10**

**What worked:**
- USGS earthquake data is genuinely useful — real, timely, includes magnitude and links
- Displacement endpoint exists with country breakdowns
- NASA FIRMS wildfire integration exists in code

**Why not 10/10:**
- -2.0: Only 5 countries, none are crisis-prone (no Bangladesh, Syria, Sudan, DRC, Yemen, Somalia)
- -1.5: Displacement data is HARDCODED STATIC — presented as real but never changes
- -1.0: No GDACS (gold standard for natural disaster alerts)
- -0.5: No IPC food security data, no INFORM Risk Index, no IOM DTM
- -0.5: Alert/notification system not functional
- -0.5: Category filtering broken (climate query returned supply_chain articles)
- -0.5: Free plan too limited (1 site for a 30-country operation)
- -0.5: No SitRep generation, no offline mode, no multi-language support

**Would pay $49/mo (Scout) if:**
1. Add GDACS integration (earthquake, tsunami, flood, cyclone alerts)
2. Connect to real UNHCR API (not static displacement data)
3. Add 30+ crisis-prone country configs
4. Fix category filtering
5. Add IPC food security and INFORM Risk Index
6. Free plan: at least 5 sites and 5 categories for NGOs
7. Working email/Slack alerts for early warning

**Comparison:** My $5K budget is better spent on free tools (GDACS, ReliefWeb API, HDX) plus ACAPS. This platform is built for corporate users, not humanitarian.

---

## ROOT CAUSE ANALYSIS: Why 4.1/10?

The score reflects **3 fundamental problems:**

### Problem 1: Platform is wide but shallow
214 feeds across 12 categories means ~17 feeds per category. But customers need DEPTH in their specific domain. A hedge fund needs 50+ financial feeds. A cyber analyst needs IOC databases. A humanitarian needs GDACS. The platform tries to serve everyone and satisfies no one deeply.

### Problem 2: Core differentiators aren't connected
The three unique features — site monitoring diff engine, AI simulation, and Chaos Index — exist independently but aren't wired into a useful workflow:
- Diff engine detects changes but doesn't trigger meaningful alerts
- Simulation exists but can't analyze a specific signal's impact
- Chaos Index is interesting but not actionable (what do I DO when it's 36.89?)

### Problem 3: Data quality undermines trust
- Static displacement data presented as live
- Consumer tech reviews in the "cyber" category
- Aviation hobbyist content in "supply chain"
- Broken sentiment analysis (all 0.0)
- Signal duplicates
- Only 5 countries

When a paying customer discovers fake data or irrelevant signals in their category, they lose trust in the entire platform. Trust is everything in intelligence.

---

## PRIORITY FIXES (What Would Move the Needle Most)

### Tier 1: Fix or Remove (Days, Not Weeks)
| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| 1 | Fix ZDNet cyber feed pollution (filter or replace) | +1.5 for cyber customer | 1 hour |
| 2 | Fix supply_chain feeds (replace aviation with logistics) | +1.5 for supply chain customer | 1 hour |
| 3 | Remove or label static displacement data as "DEMO" | Trust recovery for humanitarian | 30 min |
| 4 | Fix sentiment pipeline or remove the 0.0 display | Trust recovery for all customers | 2 hours |
| 5 | Fix category passthrough (anomaly >= 0.8 leaking into filters) | All customers | 30 min |
| 6 | Add 20+ country configs (top crisis/trading countries) | +1.0 for political, humanitarian | 4 hours |
| 7 | Fix signal deduplication (content hash, not just title) | All customers | 2 hours |

### Tier 2: Build the Missing Connectors (1-2 Weeks)
| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| 8 | Actual alert delivery (email + webhook + Slack) | +2.0 for ALL customers | 3 days |
| 9 | Connect simulation to signals (pre-fill, one-click) | +1.5 for hedge fund, political | 2 days |
| 10 | Entity extraction (NER) on signals | +1.0 for all customers | 3 days |
| 11 | Per-domain feed packs (finance pack, cyber pack, etc.) | +1.0 for targeted customers | 2 days |
| 12 | WebSocket/SSE for real-time push | +1.0 for hedge fund, supply chain | 2 days |

### Tier 3: Domain-Specific Depth (Weeks)
| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| 13 | Financial entity extraction (tickers, commodities) | Hedge fund becomes buyer | 1 week |
| 14 | STIX/TAXII + IOC feeds for cyber | Cyber becomes buyer | 1 week |
| 15 | GDACS + real UNHCR API for humanitarian | Humanitarian becomes buyer | 1 week |
| 16 | Maritime data (AIS, ports) for supply chain | Supply chain becomes buyer | 1 week |
| 17 | Industry-specific simulation templates | All customers | 2 weeks |

---

## WHAT CUSTOMERS WOULD PAY TODAY

| Customer | Would Pay | For What | If Fixed |
|----------|-----------|----------|----------|
| Marcus (Hedge Fund) | $0 today | — | $999/mo with sentiment + tickers + diff latency proof |
| Sarah (Political) | $0 today | — | $5,000/mo with 50 countries + entity tracking + scenario sim |
| James (Supply Chain) | $49/mo maybe | Geopolitical news supplement | $999/mo with maritime data + real alerting + 50 sites |
| Alex (Cyber) | $0 today | — | $199/mo with clean feeds + IOC data + MITRE ATT&CK |
| Maria (Humanitarian) | $0 today | — | $49/mo with GDACS + real displacement + 30 countries |

**Total potential revenue if Tier 1-2 fixes done: ~$7,246/mo from these 5 customers alone.**
**Total revenue today: $0.**

---

## FINAL VERDICT

OracleFlow has **exceptional architecture** — the signal pipeline, diff engine, anomaly scorer, and Chaos Index are genuinely novel. No competitor offers all four together. The 214-feed RSS aggregation is competent. The site monitoring is a real differentiator.

But the product is a **half-built intelligence platform masquerading as a complete one**. Static data presented as live, broken sentiment, polluted categories, no alert delivery, and disconnected simulation undermine the value of the good parts.

**The path to revenue:**
1. Fix data quality (Tier 1) — takes days, not weeks
2. Connect the pieces (Tier 2) — alerts + simulation + entities
3. Pick ONE vertical and go deep — the hedge fund use case is closest to paying

**The platform is 60% built. The remaining 40% is what people pay for.**
