# OracleFlow — Final Production Status

## Score Progression

| Round | Avg Score | Key Fix |
|-------|-----------|---------|
| Round 1 (initial) | 4.1/10 | First customer panel — exposed all gaps |
| Round 2 | 3.3/10 | Entities empty, countries 500, sentiment 0.0 |
| Post-R2 fixes | — | Reprocessed 1,694 signals, fixed countries, 50 configs |
| Round 3 | 6.0/10 | Entity false positives, thin domain corpus |
| Post-R3 fixes | — | Fixed entity extraction, added 18 domain feeds |
| Round 4 | 7.8/10 | Ticker aliases, sentiment expansion, search fixes |
| Post-R4 fixes | — | 30+ ticker aliases, 279 feeds, 11 importance values |

## Current System State

### Data Pipeline
- **279 RSS/API feeds** across 12 categories
- **1,419 signals** (after dedup removed 275)
- **899 signals with entities** (tickers, orgs, countries, CVEs, MITRE, IOCs, supply chain, humanitarian)
- **738 signals with non-zero sentiment** (52%)
- **11 distinct importance values** (0.45-1.0)
- **50 country configs** with government sources and political entities
- **Signal ingestion** every 15 minutes
- **Anomaly scoring** every 5 minutes
- **Page monitoring** every 30 minutes

### Features Working
- Registration + JWT auth + plan enforcement
- Interest-based personalization (5 personas)
- 30 intelligence panels (filtered by interest)
- WorldMonitor-style map with 12 layers + animations
- Site monitoring with diff engine + snapshot comparison
- AI-powered signal analysis (LLM impact assessment)
- Notification system (DB + file-based email outbox)
- Entity extraction (239 tickers + 30 aliases + orgs + countries + CVEs + MITRE ATT&CK)
- Chaos Index with 8 categories (including politics, crime, economy)
- Country risk scoring with 50 countries + trend lines
- Simulation history page
- Signal search with word-boundary matching
- 5-tier pricing (Free/Scout/Strategist/Commander/Sovereign)
- Stripe billing integration
- Multi-tenancy with org scoping

### Known Remaining Gaps
1. **New domain feeds not yet ingested** — scheduler will pick up 279 feeds within 15 minutes of restart
2. **WebSocket/SSE for real-time push** — still polling-based (60s for notifications)
3. **Simulation engine** — works but still uses MiroFish's OASIS social simulation, not domain-specific scenario modeling
4. **Email delivery** — file-based outbox, no real SMTP
5. **Some domain-specific gaps** — no dark web feeds for cyber, no STIX/TAXII, no NHC hurricane tracks
6. **No SSO/SAML** for enterprise
7. **No API rate limiting** on most endpoints (only country/brief has it)

### What Would Push Scores to 9-10/10
Based on 20 customer evaluations across 4 rounds:

| Fix | Impact | Effort |
|-----|--------|--------|
| Wait for new feeds to ingest (FDA, biotech, maritime, macro) | +0.5-1.0 for all | 15 min wait |
| Real SMTP email delivery (SendGrid/Mailgun) | +0.5 for all | 2 hours |
| WebSocket push for real-time alerts | +1.0 for finance/crypto | 1 day |
| Domain-specific simulation templates | +0.5 for all | 2 days |
| NLP-based sentiment (VADER or transformer) | +0.5 for all | 1 day |
| STIX/TAXII + IOC feeds for cyber | +2.0 for cyber | 1 week |
| Dark web monitoring | +1.5 for cyber | 2 weeks |
| SSO/SAML | +0.5 for enterprise | 1 week |

## Repository
https://github.com/pmc-tool/oracleflow
- 227+ files, 38,000+ lines
- 279 RSS feeds
- 50 country configs
- 30 intelligence panels
- 12 map layers with animations
