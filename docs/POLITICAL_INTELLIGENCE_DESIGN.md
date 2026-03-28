# OracleFlow Political Intelligence Module: Complete Design

## Target-Centric Monitoring Pipeline for Political Organizations

---

## 1. COMPLETE USER JOURNEY

### Screen 1: Registration (existing) + Organization Profile (new step)

After the user registers, they currently land on InterestPicker (persona selection).
We ADD a new step between registration and persona selection:

```
[Register] -> [Organization Profile] -> [InterestPicker] -> [Add Targets] -> [Target Dashboard]
```

**Organization Profile screen** asks:
- "What does your organization do?"
  - Political party / NGO / Media / Corporate / Government / Other
- "Which country are you based in?" (dropdown, defaults based on IP)
- "What is your primary goal?"
  - Monitor competitors / Track media coverage / Intelligence gathering / Risk assessment

This data is saved to `Organization.org_type` and `Organization.country_code` (new fields).

When "Political party" + "Monitor competitors" is selected, the system:
1. Auto-selects the "political" persona
2. Activates country-specific feed bundle for their country
3. Redirects to the **Add Targets** screen instead of the generic Intel dashboard

### Screen 2: Add Monitoring Targets (NEW: `/targets/add`)

```
+------------------------------------------------------------------+
|  Who do you want to monitor?                                      |
|                                                                   |
|  [Search: "Jamaat-e-Islami Bangladesh"              ] [Search]    |
|                                                                   |
|  --- Search Results ---                                           |
|  [x] Jamaat-e-Islami Bangladesh                                   |
|      Type: Political Party | Country: BD                          |
|      Website: jamaat-bd.org (detected)                            |
|      Facebook: facebook.com/jamaborbd (detected)                  |
|      YouTube: (not found - add manually?)                         |
|      Keywords: jamaat, JI, islamist, ameer                        |
|      Leaders: [auto-suggested from registry/LLM]                  |
|                                                                   |
|  [Confirm & Start Monitoring]         [Add Another Target]        |
+------------------------------------------------------------------+
```

**What happens on "Search":**
1. Backend checks the country registry YAML (bangladesh.yaml already has `political_entities`)
2. If not in registry, uses LLM to identify the entity and suggest web presence
3. Returns a `TargetDiscoveryResult` with:
   - Confirmed name + aliases
   - Detected website URL
   - Detected social media pages
   - Suggested keywords
   - Known leaders/sub-entities

**On "Confirm":**
1. Creates a `MonitoringTarget` record
2. Creates `MonitoredSite` records for each discovered URL
3. Creates `Entity` records for the target + its leaders
4. Creates `TargetFeedSource` records linking RSS feeds to this target
5. Triggers background discovery on the target's website
6. Activates keyword-matching on all incoming signals for this target

### Screen 3: Target Dashboard (NEW: `/targets/:targetId`)

Replaces the 30-panel generic Intel view with a focused 6-panel layout:

```
+------------------------------------------------------------------+
| [Target Selector: Jamaat-e-Islami v]  [Add Target]  [All Targets] |
+------------------------------------------------------------------+
|                                                                   |
| +--ACTIVITY FEED (half width)------+ +--SENTIMENT CHART---------+ |
| | [Today] [This Week] [This Month] | | Line chart: sentiment    | |
| |                                   | | over 7/30 days           | |
| | 14:32 - "Jamaat calls for hartal" | | Positive ===---          | |
| |   Source: bdnews24  Score: 0.82   | | Negative    ---===       | |
| |                                   | |                          | |
| | 12:15 - "JI leader arrested in.." | | [Overlay: BNP sentiment] | |
| |   Source: Daily Star  Score: 0.91 | +---------------------------+
| |                                   |                             |
| | 09:01 - Website changed: Events.. | +--COMPARISON CHART--------+
| |   Source: site_monitor            | | Bar: mentions this week  |
| +-----------------------------------+ | BNP:    ========  (124)  |
|                                       | Jamaat: =====     (87)   |
| +--WEBSITE CHANGES---------+ +--KEY PEOPLE------------------+    |
| | jamaat-bd.org             | | Shafiqur Rahman (Ameer)      |   |
| | Last check: 2 hours ago  | |   3 mentions today           |   |
| | Homepage: no change       | | Mia Golam Parwar (SG)        |   |
| | /events: 2 new events     | |   1 mention today            |   |
| | /news: 5 new articles     | |                              |   |
| +---------------------------+ +------------------------------+   |
+------------------------------------------------------------------+
```

### Screen 4: All Targets Overview (NEW: `/targets`)

```
+------------------------------------------------------------------+
| MY MONITORING TARGETS                          [+ Add Target]     |
+------------------------------------------------------------------+
| Target              | Type     | Signals | Sentiment | Alert     |
|---------------------|----------|---------|-----------|-----------|
| Jamaat-e-Islami     | Party    | 87 /wk  | -0.3      | 2 new    |
| Hefazat-e-Islam     | Org      | 23 /wk  | -0.5      | 0        |
| Bangladesh AL       | Party    | 156 /wk | +0.1      | 5 new    |
+------------------------------------------------------------------+
```

### Screen 5: Existing Intel Dashboard (MODIFIED)

The existing `/intel` view gets a new "My Targets" tab alongside existing categories.
When the user has targets configured, the default view filters signals to show
only signals matching their targets' keywords, instead of all global signals.

---

## 2. DATABASE MODELS

### New Model: `MonitoringTarget`

```python
# File: backend/app/oracleflow/models/target.py

class MonitoringTarget(TimestampMixin, Base):
    """A monitoring target -- WHO the organization is watching."""
    __tablename__ = "monitoring_targets"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name            = Column(String(512), nullable=False)
    target_type     = Column(String(50), nullable=False)
        # Values: political_party, company, person, organization, government, media
    country_code    = Column(String(10), nullable=True)
    description     = Column(Text, nullable=True)
    aliases_json    = Column(JSON, default=list)
        # e.g. ["Jamaat", "JI", "Bangladesh Jamaat-e-Islami"]
    keywords_json   = Column(JSON, default=list)
        # e.g. ["jamaat", "জামায়াত", "ameer", "hartal"]
    social_links_json = Column(JSON, default=dict)
        # e.g. {"facebook": "https://facebook.com/...", "twitter": "...", "youtube": "..."}
    website_url     = Column(String(2048), nullable=True)
    is_active       = Column(Boolean, default=True)
    metadata_json   = Column(JSON, nullable=True)
        # Flexible store for anything else: logo_url, founding_date, ideology, etc.

    # Relationships
    feeds    = relationship("TargetFeedSource", back_populates="target", cascade="all, delete-orphan")
    entities = relationship("TargetEntity", back_populates="target", cascade="all, delete-orphan")
    sites    = relationship("TargetSite", back_populates="target", cascade="all, delete-orphan")
```

### New Model: `TargetFeedSource`

```python
class TargetFeedSource(Base):
    """An RSS/news feed specifically linked to a monitoring target."""
    __tablename__ = "target_feed_sources"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("monitoring_targets.id", ondelete="CASCADE"), nullable=False)
    feed_url  = Column(String(2048), nullable=False)
    feed_type = Column(String(50), nullable=False, default="rss")
        # Values: rss, youtube, twitter_rss, facebook_rss, google_news
    name      = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)

    target = relationship("MonitoringTarget", back_populates="feeds")
```

### New Model: `TargetEntity`

```python
class TargetEntity(Base):
    """Links a MonitoringTarget to Entity records (leaders, sub-orgs)."""
    __tablename__ = "target_entities"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    target_id   = Column(Integer, ForeignKey("monitoring_targets.id", ondelete="CASCADE"), nullable=False)
    entity_id   = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    role        = Column(String(100), nullable=True)  # e.g. "ameer", "secretary_general", "spokesperson"

    target = relationship("MonitoringTarget", back_populates="entities")
    entity = relationship("Entity")
```

### New Model: `TargetSite`

```python
class TargetSite(Base):
    """Links a MonitoringTarget to a MonitoredSite."""
    __tablename__ = "target_sites"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("monitoring_targets.id", ondelete="CASCADE"), nullable=False)
    site_id   = Column(Integer, ForeignKey("monitored_sites.id", ondelete="CASCADE"), nullable=False)

    target = relationship("MonitoringTarget", back_populates="sites")
    site   = relationship("MonitoredSite")
```

### New Model: `TargetSignalMatch`

```python
class TargetSignalMatch(Base):
    """Records which signals matched which targets (via keywords/entities)."""
    __tablename__ = "target_signal_matches"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("monitoring_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True)
    match_type = Column(String(50), nullable=False)
        # Values: keyword, entity, source_feed, website_change
    match_detail = Column(String(512), nullable=True)  # which keyword matched, etc.
    matched_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### Modified Existing Models

**Organization** (add 2 columns):
```python
org_type     = Column(String(50), nullable=True)   # political_party, corporate, ngo, media, government
country_code = Column(String(10), nullable=True)    # ISO 2-letter
```

**Signal** (add 1 column -- optional, for fast filtering):
```python
target_ids_json = Column(JSON, nullable=True)  # [1, 3] -- targets this signal matched
```

---

## 3. API ENDPOINTS

### Targets API (NEW Blueprint: `targets_bp`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/targets/` | List all targets for the org |
| `POST` | `/api/targets/` | Create a new monitoring target |
| `GET` | `/api/targets/:id` | Get target detail (with feeds, entities, sites) |
| `PUT` | `/api/targets/:id` | Update target (name, keywords, social links) |
| `DELETE` | `/api/targets/:id` | Deactivate a target |
| `GET` | `/api/targets/:id/signals` | Get signals matching this target (paginated) |
| `GET` | `/api/targets/:id/sentiment` | Get sentiment time-series for this target |
| `GET` | `/api/targets/:id/activity` | Get combined activity feed (signals + site changes) |
| `POST` | `/api/targets/:id/feeds` | Add a feed source to a target |
| `DELETE` | `/api/targets/:id/feeds/:feedId` | Remove a feed source |
| `GET` | `/api/targets/compare` | Compare multiple targets (mentions, sentiment) |

### Target Discovery API (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/targets/discover` | Search for a target and auto-discover web presence |

**Request:**
```json
{
  "query": "Jamaat-e-Islami Bangladesh",
  "country_code": "BD",
  "target_type": "political_party"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "Jamaat-e-Islami Bangladesh",
    "aliases": ["Jamaat", "JI", "Bangladesh Jamaat-e-Islami"],
    "country_code": "BD",
    "target_type": "political_party",
    "website": "https://www.jamaat-bd.org",
    "social_links": {
      "facebook": "https://www.facebook.com/jamaborbd",
      "youtube_channel_id": null,
      "twitter": null
    },
    "suggested_keywords": ["jamaat", "জামায়াত", "ameer", "hartal", "islami"],
    "suggested_leaders": [
      {"name": "Shafiqur Rahman", "role": "Ameer"},
      {"name": "Mia Golam Parwar", "role": "Secretary General"}
    ],
    "suggested_feeds": [
      {"url": "https://www.thedailystar.net/rss", "name": "Daily Star", "type": "rss"},
      {"url": "https://bdnews24.com/feed", "name": "bdnews24", "type": "rss"},
      {"url": "https://en.prothomalo.com/feed", "name": "Prothom Alo (EN)", "type": "rss"},
      {"url": "https://www.dhakatribune.com/feed", "name": "Dhaka Tribune", "type": "rss"}
    ],
    "country_bundle_available": true
  }
}
```

### Modified Existing Endpoints

**`GET /api/signals/`** -- add parameter:
- `target_id` (int, optional): Filter signals to only those matching this target

**`GET /api/countries/:code`** -- already exists, no change needed.

---

## 4. FRONTEND PAGES & COMPONENTS

### New Pages (Vue views)

| File | Route | Description |
|------|-------|-------------|
| `TargetsView.vue` | `/targets` | List all monitoring targets with summary stats |
| `TargetDetailView.vue` | `/targets/:targetId` | Target-centric dashboard (6 panels) |
| `TargetAddView.vue` | `/targets/add` | Search + discover + create target wizard |
| `OrgProfileView.vue` | `/onboarding/org` | Post-registration org type/country picker |

### New Components

| File | Used In | Description |
|------|---------|-------------|
| `TargetActivityFeed.vue` | TargetDetailView | Scrolling feed of signals matching target |
| `TargetSentimentChart.vue` | TargetDetailView | Line chart of sentiment over time |
| `TargetComparisonChart.vue` | TargetDetailView | Bar chart comparing target vs. own org |
| `TargetWebsiteChanges.vue` | TargetDetailView | Shows recent diffs from target's monitored sites |
| `TargetKeyPeople.vue` | TargetDetailView | Cards for each linked entity/person |
| `TargetDiscoverySearch.vue` | TargetAddView | Search input + results for discovery |
| `TargetCard.vue` | TargetsView | Summary card showing target name + stats |

### Modified Existing Components

| File | Change |
|------|--------|
| `OracleNav.vue` | Add "Targets" nav link between "Sites" and "Signals" |
| `IntelView.vue` | Add "My Targets" tab; filter signals by target keywords when active |
| `InterestPicker.vue` | After persona selection, redirect political users to `/targets/add` |
| `CategoryTabs.vue` | Add "Targets" category option |

### Router Changes

```javascript
// Add to router/index.js
import TargetsView from '../views/TargetsView.vue'
import TargetDetailView from '../views/TargetDetailView.vue'
import TargetAddView from '../views/TargetAddView.vue'
import OrgProfileView from '../views/OrgProfileView.vue'

// New routes:
{ path: '/targets',           name: 'Targets',       component: TargetsView },
{ path: '/targets/add',       name: 'TargetAdd',     component: TargetAddView },
{ path: '/targets/:targetId', name: 'TargetDetail',  component: TargetDetailView, props: true },
{ path: '/onboarding/org',    name: 'OrgProfile',    component: OrgProfileView },
```

### API Client Additions

```javascript
// Add to frontend/src/api/intelligence.js

// Targets
export const listTargets = () => service.get('/api/targets/')
export const createTarget = (data) => service.post('/api/targets/', data)
export const getTarget = (id) => service.get(`/api/targets/${id}`)
export const updateTarget = (id, data) => service.put(`/api/targets/${id}`, data)
export const deleteTarget = (id) => service.delete(`/api/targets/${id}`)
export const getTargetSignals = (id, params = {}) => service.get(`/api/targets/${id}/signals`, { params })
export const getTargetSentiment = (id, params = {}) => service.get(`/api/targets/${id}/sentiment`, { params })
export const getTargetActivity = (id, params = {}) => service.get(`/api/targets/${id}/activity`, { params })
export const addTargetFeed = (id, feed) => service.post(`/api/targets/${id}/feeds`, feed)
export const removeTargetFeed = (id, feedId) => service.delete(`/api/targets/${id}/feeds/${feedId}`)
export const compareTargets = (targetIds) => service.get('/api/targets/compare', { params: { ids: targetIds.join(',') } })
export const discoverTarget = (query) => service.post('/api/targets/discover', query)
```

---

## 5. TARGET DISCOVERY PIPELINE (Backend Detail)

### How `POST /api/targets/discover` works internally

```python
# backend/app/oracleflow/targets/discovery.py

class TargetDiscoveryService:
    """Discovers web presence for a monitoring target."""

    def discover(self, query: str, country_code: str, target_type: str) -> TargetDiscoveryResult:
        results = TargetDiscoveryResult(query=query)

        # Step 1: Check country registry YAML
        registry = RegistryLoader()
        country = registry.get_country(country_code)
        if country:
            for pe in country.sources.political_entities:
                if self._fuzzy_match(query, pe.name, pe.aliases):
                    results.name = pe.name
                    results.aliases = pe.aliases
                    results.website = pe.website
                    results.leaders.append({"name": pe.leader, "role": "leader"})
                    break

        # Step 2: If not in registry, use LLM to identify
        if not results.name:
            llm_result = self._llm_identify(query, country_code, target_type)
            results.merge(llm_result)

        # Step 3: Auto-discover web presence
        if results.website:
            # Validate the URL is reachable
            results.website_verified = self._check_url(results.website)

        # Step 4: Build social media links
        # Facebook: search for public page (or use known mapping)
        # YouTube: search for official channel, build RSS URL
        # Twitter: search for official handle
        results.social_links = self._discover_social(results.name, country_code)

        # Step 5: Suggest keywords (name + aliases + Bangla transliteration)
        results.suggested_keywords = self._build_keywords(results)

        # Step 6: Attach country feed bundle
        if country:
            results.suggested_feeds = self._country_news_feeds(country_code)

        return results
```

### Country Feed Bundles (hardcoded for Phase 1)

```python
# backend/app/oracleflow/targets/country_feeds.py

COUNTRY_FEED_BUNDLES = {
    "BD": {
        "news": [
            {"url": "https://www.thedailystar.net/frontpage/rss.xml", "name": "Daily Star"},
            {"url": "https://bdnews24.com/feed", "name": "bdnews24"},
            {"url": "https://en.prothomalo.com/feed", "name": "Prothom Alo (EN)"},
            {"url": "https://www.dhakatribune.com/feed", "name": "Dhaka Tribune"},
            {"url": "https://www.newagebd.net/rss", "name": "New Age BD"},
            {"url": "https://www.tbsnews.net/feed", "name": "TBS News"},
        ],
        "government": [
            {"url": "https://www.bangladesh.gov.bd", "name": "BD Govt Portal"},
            {"url": "https://www.ecs.gov.bd", "name": "Election Commission"},
        ],
        "google_news": [
            # Google News RSS for specific queries -- works without API key
            {"url": "https://news.google.com/rss/search?q=bangladesh+politics&hl=en-BD&gl=BD", "name": "Google News: BD Politics"},
        ]
    },
    "JM": {
        "news": [
            {"url": "https://www.jamaicaobserver.com/feed/", "name": "Jamaica Observer"},
            {"url": "https://jamaica-gleaner.com/feed", "name": "Jamaica Gleaner"},
        ],
        # ... etc
    },
    # Add more countries as needed
}
```

### How Social Media Works (MVP approach)

**YouTube** -- already has RSS, works today:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```
Just add as a TargetFeedSource with feed_type="youtube". The existing RSS parser handles it.

**Facebook** -- public page posts via RSS bridge:
- Option A: Use an RSS bridge service (e.g., rss-bridge.org or self-hosted)
  `https://rss-bridge.example.com/?action=display&bridge=Facebook&context=User&u=pagename&format=Atom`
- Option B: For MVP, just monitor the Facebook page URL as a MonitoredSite (detect changes)
- Option C: If budget allows, use CrowdTangle replacement (Meta Content Library API)

**Twitter/X** -- via RSS bridge services:
- Nitter instances provide RSS: `https://nitter.net/username/rss`
- Or use Twitter API v2 (requires paid access)
- For MVP: add as MonitoredSite and detect changes, or use Google News RSS filtered to twitter.com

**Google News RSS** -- free, no API key, works today:
```
https://news.google.com/rss/search?q="Jamaat-e-Islami"+Bangladesh&hl=en-BD&gl=BD
```
This is the single most powerful MVP approach. Build a Google News RSS URL per target and add it as a TargetFeedSource. The existing RSS ingest pipeline handles everything.

---

## 6. SIGNAL MATCHING ENGINE

### How signals get tagged to targets

```python
# backend/app/oracleflow/targets/matcher.py

class TargetSignalMatcher:
    """Matches incoming signals against active monitoring targets."""

    def __init__(self, db: Session):
        self.db = db
        self._targets_cache = None

    def load_targets(self, org_id: int = None):
        """Load all active targets (optionally for a specific org)."""
        stmt = select(MonitoringTarget).where(MonitoringTarget.is_active == True)
        if org_id:
            stmt = stmt.where(MonitoringTarget.organization_id == org_id)
        self._targets_cache = list(self.db.execute(stmt).scalars().all())

    def match_signal(self, signal: Signal) -> list[TargetSignalMatch]:
        """Check if a signal matches any monitoring targets by keywords."""
        matches = []
        text = ((signal.title or '') + ' ' + (signal.summary or '')).lower()

        for target in self._targets_cache:
            # Check keywords
            all_keywords = (target.keywords_json or []) + (target.aliases_json or []) + [target.name.lower()]
            for kw in all_keywords:
                if kw.lower() in text:
                    matches.append(TargetSignalMatch(
                        target_id=target.id,
                        signal_id=signal.id,
                        match_type="keyword",
                        match_detail=kw,
                    ))
                    break  # One match per target is enough

        return matches
```

### Integration point: called after every signal ingest

In `backend/app/oracleflow/feeds/rss.py` `fetch_global_feeds()`, after `db.flush()`:

```python
# After signals are created, match them against targets
from app.oracleflow.targets.matcher import TargetSignalMatcher
matcher = TargetSignalMatcher(db)
matcher.load_targets()  # All orgs
for signal in signals:
    matches = matcher.match_signal(signal)
    for m in matches:
        db.add(m)
db.flush()
```

---

## 7. PHASED IMPLEMENTATION PLAN

### Phase 1: MonitoringTarget CRUD + Google News RSS (1-2 days)

**What it delivers:** Users can define targets, and the system auto-generates Google News RSS feeds for each target and ingests signals mentioning them.

**Backend (day 1):**
- [ ] Create `models/target.py` with MonitoringTarget, TargetFeedSource, TargetEntity, TargetSite, TargetSignalMatch
- [ ] Add migration in `database.py` to create new tables
- [ ] Create `api/targets.py` blueprint with CRUD endpoints (list, create, get, update, delete)
- [ ] Register `targets_bp` in `api/__init__.py`
- [ ] Create `targets/country_feeds.py` with COUNTRY_FEED_BUNDLES for BD (and 2-3 other countries)
- [ ] Create `targets/matcher.py` with keyword matching
- [ ] Integrate matcher into `feeds/rss.py` after signal creation
- [ ] Add `target_id` filter to `GET /api/signals/`
- [ ] Add Google News RSS URL generation: `f"https://news.google.com/rss/search?q={urllib.parse.quote(target.name)}&hl=en"`

**Frontend (day 2):**
- [ ] Create `TargetsView.vue` -- list page with target cards
- [ ] Create `TargetAddView.vue` -- simple form (name, type, country, keywords, website URL)
- [ ] Create `TargetDetailView.vue` -- activity feed (reuses SignalsView with target_id filter)
- [ ] Add routes to `router/index.js`
- [ ] Add API functions to `intelligence.js`
- [ ] Add "Targets" link to `OracleNav.vue`

**What works after Phase 1:**
- BNP signs up, creates target "Jamaat-e-Islami", enters country BD
- System generates Google News RSS feed for "Jamaat-e-Islami Bangladesh"
- Existing RSS ingest pipeline picks up stories about Jamaat every 15 minutes
- User sees a filtered signal feed for Jamaat on the target detail page
- Keywords: manual entry for now

**No new infrastructure needed.** Uses existing RSS pipeline, existing DB (SQLite/Postgres), existing scheduler.

---

### Phase 2: Target Discovery + Country Bundles + Sentiment (3-5 days)

**What it delivers:** Auto-discovery of target web presence, country-specific news feeds auto-added, sentiment tracking.

**Backend:**
- [ ] Create `targets/discovery.py` with TargetDiscoveryService
- [ ] `POST /api/targets/discover` endpoint
- [ ] Enhance bangladesh.yaml with news sources, political entities, social links
- [ ] Create/enhance YAML configs for 10 high-demand countries
- [ ] `GET /api/targets/:id/sentiment` -- aggregate sentiment_score from TargetSignalMatch + Signal over time
- [ ] `GET /api/targets/compare` -- multi-target comparison endpoint
- [ ] Auto-generate YouTube RSS feeds when channel ID is known
- [ ] Add `org_type` and `country_code` columns to Organization model

**Frontend:**
- [ ] Create `TargetDiscoverySearch.vue` component with search + results display
- [ ] Upgrade `TargetAddView.vue` to use discovery (search -> review -> confirm)
- [ ] Create `TargetSentimentChart.vue` (line chart, use existing d3 dependency)
- [ ] Create `TargetComparisonChart.vue` (bar chart)
- [ ] Create `OrgProfileView.vue` for post-registration onboarding step
- [ ] Wire onboarding flow: Register -> OrgProfile -> TargetAdd -> TargetDetail

**No new infrastructure needed.** Discovery uses LLM (already configured in config.py) + hardcoded country bundles. Sentiment uses existing `sentiment_score` on signals.

---

### Phase 3: Website Monitoring + Social Media + Alerts (5-7 days)

**What it delivers:** Auto-monitors target websites for changes, basic social media ingestion, and target-specific alerts.

**Backend:**
- [ ] When target is created with a website, auto-create MonitoredSite + run discovery
- [ ] Create `TargetWebsiteChanges.vue` -- reuses existing PageDiff data but scoped to target's sites
- [ ] Facebook page monitoring via RSS bridge (self-hosted rss-bridge)
- [ ] Twitter/X monitoring via Nitter RSS or similar bridge
- [ ] Target-specific alert rules: "Alert me when Jamaat anomaly > 0.7"
- [ ] Extend AlertRuleDB with `target_id` field
- [ ] Push notifications when target activity spikes

**Frontend:**
- [ ] Create `TargetWebsiteChanges.vue` component
- [ ] Create `TargetKeyPeople.vue` component (linked entities)
- [ ] Add alert configuration to target detail page
- [ ] Add "My Targets" tab to IntelView.vue

**New infrastructure (optional):** Self-hosted RSS bridge for Facebook/Twitter. Can use free hosted instances for MVP.

---

### Phase 4: Advanced Intelligence (7-14 days)

**What it delivers:** LLM-powered analysis, geographic activity mapping, Bangla language support, historical trend analysis.

**Backend:**
- [ ] LLM-powered target intelligence briefs ("What is Jamaat doing this week?")
- [ ] Geographic activity mapping (extract district/division mentions from signals)
- [ ] Bangla keyword matching (extend matcher to handle Bengali script)
- [ ] Network graph: visualize relationships between targets and their sub-entities
- [ ] Target activity prediction (based on historical patterns)
- [ ] Bulk signal re-processing to backfill target matches on historical data

**Frontend:**
- [ ] Target intelligence brief panel (LLM-generated summary)
- [ ] Geographic activity heatmap for Bangladesh (districts)
- [ ] Entity relationship graph visualization (reuse existing GraphPanel.vue)
- [ ] Historical trend analysis view

**New infrastructure:** May need a Bangla NER model or translation service. Could use existing LLM with Bangla prompts.

---

## 8. WHAT CAN BE DONE WITHOUT NEW INFRASTRUCTURE

### Uses only existing infrastructure (SQLite/Postgres + RSS pipeline + LLM):

| Feature | How |
|---------|-----|
| MonitoringTarget CRUD | New DB tables, standard Flask API |
| Google News RSS per target | Generate URL, add to RSS ingest pipeline |
| Keyword matching on signals | Python string matching in existing ingest loop |
| Country feed bundles | Hardcoded Python dict, feeds go through existing RSS parser |
| Target signal filtering | SQL WHERE clause on existing signals table |
| Sentiment over time | Aggregate existing `sentiment_score` from matched signals |
| Target comparison | SQL GROUP BY on TargetSignalMatch |
| Website change detection | Existing MonitoredSite + PageDiff + DiscoveryService |
| YouTube RSS | Standard RSS feed, existing parser handles it |
| Target discovery (basic) | LLM call (already configured) + registry YAML lookup |
| Target alerts | Extend existing AlertRuleDB with target_id |

### Needs new services/infrastructure:

| Feature | What's needed |
|---------|---------------|
| Facebook monitoring | RSS bridge service (self-hosted or free hosted) |
| Twitter/X monitoring | Nitter instance or Twitter API v2 ($100/mo) |
| Bangla NER | Bangla language model or translation API |
| Real-time social monitoring | Streaming API or frequent polling service |
| Geographic mapping (BD districts) | Bangladesh GeoJSON + district extraction logic |

---

## 9. BANGLADESH.YAML UPGRADE (Phase 2)

The current bangladesh.yaml is minimal. Here is the upgraded version:

```yaml
country: Bangladesh
code: BD
region: south_asia
languages:
  - bn
  - en
timezone: Asia/Dhaka
proxy_pool: ""

sources:
  news:
    - url: https://www.thedailystar.net
      frequency: "15m"
      anti_bot: low
    - url: https://bdnews24.com
      frequency: "15m"
      anti_bot: low
    - url: https://en.prothomalo.com
      frequency: "15m"
      anti_bot: low
    - url: https://www.dhakatribune.com
      frequency: "15m"
      anti_bot: low
    - url: https://www.newagebd.net
      frequency: "30m"
      anti_bot: low
    - url: https://www.tbsnews.net
      frequency: "30m"
      anti_bot: low
    - url: https://www.risingbd.com
      frequency: "30m"
      anti_bot: low

  reddit:
    - subreddit: bangladesh
      frequency: "30m"

  government:
    - url: https://www.bangladesh.gov.bd
      type: government_portal
      frequency: "2h"
    - url: https://www.ecs.gov.bd
      type: election_commission
      frequency: "2h"
    - url: https://www.parliament.gov.bd
      type: parliament
      frequency: "6h"

  social:
    facebook_pages:
      - BNPOfficial
      - awaborbd
      - jamaborbd
    twitter_accounts:
      - bdnews24
      - dailaborahon

  political_entities:
    - name: Bangladesh Nationalist Party
      aliases: ["BNP", "বিএনপি"]
      website: https://www.bnpbd.org
      leader: Tarique Rahman
    - name: Jamaat-e-Islami Bangladesh
      aliases: ["Jamaat", "JI", "জামায়াত", "Bangladesh Jamaat"]
      website: https://www.jamaat-bd.org
      leader: Shafiqur Rahman
    - name: Bangladesh Awami League
      aliases: ["AL", "Awami League", "আওয়ামী লীগ"]
      website: https://www.albd.org
      leader: Sheikh Hasina
    - name: Jatiya Party
      aliases: ["JP", "জাতীয় পার্টি"]
      website: https://www.jatiyaparty.org.bd
      leader: GM Quader
    - name: Muhammad Yunus
      type: person
      role: Chief Adviser
```

---

## 10. KEY ARCHITECTURAL DECISIONS

1. **Target-Signal matching is done at ingest time, not query time.**
   We create TargetSignalMatch records when signals arrive. This makes dashboard queries fast (simple JOINs) instead of running keyword searches on every page load.

2. **Google News RSS is the MVP secret weapon.**
   It requires zero infrastructure, zero API keys, and covers most news sources globally. One URL per target gives you instant monitoring.

3. **MonitoringTarget is organization-scoped, not user-scoped.**
   All users in the BNP organization see the same targets. Individual users can configure which targets they get alerts for.

4. **The existing Entity model is reused, not replaced.**
   TargetEntity links a MonitoringTarget to Entity records. This lets us reuse the existing entity extraction, relationship mapping, and graph visualization.

5. **Country feed bundles are hardcoded Python dicts, not YAML.**
   YAML configs are for countries themselves. Feed bundles are operational data that changes with RSS URL availability and should be easy to update in code.

6. **Social media is treated as RSS where possible.**
   YouTube has native RSS. Facebook and Twitter can use RSS bridges. This avoids building custom scrapers and lets the existing RSS pipeline handle everything.

7. **The target dashboard is a new view, not a modification of IntelView.**
   IntelView (30 panels) remains for geopolitical analysts who want the broad view. TargetDetailView is a focused 6-panel layout for target monitoring. Users choose which to use.
