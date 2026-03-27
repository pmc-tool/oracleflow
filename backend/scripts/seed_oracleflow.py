"""Seed OracleFlow data inside MiroFish's database."""

import sys
import os
import random
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.oracleflow.models.base import Base
from app.oracleflow.models.site import MonitoredSite, SitePage, PageSnapshot, PageDiff
from app.oracleflow.models.entity import Entity, EntitySource, EntityRelationship
from app.oracleflow.models.signal import Signal, Simulation, Alert, ChaosIndex


def now(): return datetime.now(timezone.utc)
def hours_ago(h): return now() - timedelta(hours=h)
def days_ago(d): return now() - timedelta(days=d)


def seed():
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///oracleflow.db')
    engine = create_engine(db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        # Sites
        sites = []
        for url, domain, status, pages in [
            ("https://pnpjamaica.com", "pnpjamaica.com", "active", 12),
            ("https://jlp.org.jm", "jlp.org.jm", "active", 8),
            ("https://jamaicaobserver.com", "jamaicaobserver.com", "active", 45),
            ("https://guardian.co.tt", "guardian.co.tt", "active", 23),
            ("https://barbadostoday.bb", "barbadostoday.bb", "discovering", 0),
        ]:
            s = MonitoredSite(url=url, domain=domain, status=status, discovered_pages_count=pages,
                              created_at=days_ago(random.randint(1, 14)), updated_at=hours_ago(random.randint(0, 48)))
            db.add(s)
            sites.append(s)
        db.flush()

        # Pages for first site
        pages = []
        for path, ptype, imp, freq in [
            ("/", "homepage", 0.9, "30m"), ("/healthcare", "policy_page", 0.85, "2h"),
            ("/leadership", "team_page", 0.7, "2h"), ("/news", "news_index", 0.9, "30m"),
            ("/education", "policy_page", 0.8, "2h"), ("/events", "events", 0.6, "2h"),
            ("/donate", "fundraising", 0.4, "2h"), ("/climate-policy", "policy_page", 0.75, "2h"),
        ]:
            p = SitePage(site_id=sites[0].id, url=f"https://pnpjamaica.com{path}", path=path,
                         page_type=ptype, importance_score=imp, monitoring_frequency=freq,
                         anti_bot_level="low", is_active=True, last_crawled=hours_ago(random.randint(0, 6)))
            db.add(p)
            pages.append(p)
        db.flush()

        # Snapshots + Diffs
        for p in pages:
            old = PageSnapshot(page_id=p.id, content_text=f"Old {p.path}", content_html=f"<h1>{p.path}</h1>",
                               content_hash=f"{random.getrandbits(128):032x}", metadata_json={"title": p.path},
                               captured_at=hours_ago(48))
            new = PageSnapshot(page_id=p.id, content_text=f"New {p.path} updated", content_html=f"<h1>{p.path} v2</h1>",
                               content_hash=f"{random.getrandbits(128):032x}", metadata_json={"title": p.path},
                               captured_at=hours_ago(2))
            db.add(old)
            db.add(new)
            db.flush()
            if random.random() > 0.5:
                db.add(PageDiff(page_id=p.id, old_snapshot_id=old.id, new_snapshot_id=new.id,
                                diff_type="content_changed", diff_summary=f"{p.path} was updated",
                                diff_detail_json={"change_pct": random.uniform(5, 40)}, detected_at=hours_ago(2)))
        db.flush()

        # Entities
        entities = []
        for name, etype, cc, meta in [
            ("Mark Golding", "person", "JM", {"role": "PNP President"}),
            ("Andrew Holness", "person", "JM", {"role": "Prime Minister", "party": "JLP"}),
            ("Lisa Hanna", "person", "JM", {"role": "PNP VP"}),
            ("Dr. Sarah Chen", "person", "JM", {"role": "Shadow Health Minister"}),
            ("Peter Phillips", "person", "JM", {"role": "Former PNP President"}),
            ("Keith Rowley", "person", "TT", {"role": "PM Trinidad"}),
            ("Mia Mottley", "person", "BB", {"role": "PM Barbados"}),
            ("People's National Party", "political_party", "JM", {"aliases": ["PNP"]}),
            ("Jamaica Labour Party", "political_party", "JM", {"aliases": ["JLP"]}),
            ("Jamaica Observer", "media", "JM", {}),
            ("Trade Union Congress", "organization", "JM", {}),
        ]:
            e = Entity(name=name, entity_type=etype, country_code=cc, metadata_json=meta,
                       created_at=days_ago(random.randint(1, 10)), updated_at=hours_ago(random.randint(0, 48)))
            db.add(e)
            entities.append(e)
        db.flush()

        # Entity sources
        for idx, stype, url, conf in [
            (0, "twitter", "https://twitter.com/markjgolding", 0.95),
            (0, "facebook", "https://facebook.com/MarkGoldingJM", 0.90),
            (1, "twitter", "https://twitter.com/AndrewHolnessJM", 0.98),
            (2, "twitter", "https://twitter.com/LisaHannaJA", 0.92),
            (6, "twitter", "https://twitter.com/MiaMottley", 0.95),
        ]:
            db.add(EntitySource(entity_id=entities[idx].id, source_type=stype, source_url=url,
                                confidence_score=conf, discovered_at=days_ago(random.randint(1, 7))))
        db.flush()

        # Relationships
        for fi, ti, rtype, strength, evidence in [
            (0, 2, "political_ally", 0.85, "PNP leadership team"),
            (0, 1, "political_rival", 0.90, "Opposition leaders"),
            (0, 4, "political_ally", 0.60, "Former colleagues"),
            (0, 10, "supporter", 0.70, "Union endorsement signals"),
            (2, 4, "political_ally", 0.55, "Increasing co-appearances"),
        ]:
            db.add(EntityRelationship(from_entity_id=entities[fi].id, to_entity_id=entities[ti].id,
                                      relationship_type=rtype, strength=strength, source_evidence=evidence))
        db.flush()

        # Signals
        signal_objs = []
        for src, stype, cat, cc, title, summary, sent, anom, imp, ts in [
            ("scrapling", "page_content_changed", "politics", "JM",
             "PNP Updated Healthcare Policy", "Healthcare page updated with free hospital visits commitment", 0.72, 0.78, 0.85, hours_ago(2)),
            ("scrapling", "new_page_detected", "politics", "JM",
             "PNP Added Climate Policy Section", "New climate policy 2026 section added to website", 0.55, 0.65, 0.70, hours_ago(5)),
            ("scrapling", "metadata_changed", "politics", "JM",
             "PNP Homepage Title Changed to Healthcare First", "Campaign messaging pivot detected", 0.60, 0.72, 0.75, hours_ago(8)),
            ("scrapling", "new_page_detected", "politics", "JM",
             "New Shadow Health Minister Appointed", "Dr. Sarah Chen added to leadership page", 0.65, 0.80, 0.82, hours_ago(12)),
            ("scrapling", "page_content_changed", "economy", "JM",
             "JLP Economy Page Updated", "New infrastructure spending figures totaling $2.3B", 0.50, 0.55, 0.65, hours_ago(18)),
            ("rss", "news_article", "politics", "JM",
             "Jamaica Election Polls Show Tight Race", "PNP 48% vs JLP 45%, healthcare top issue", 0.40, 0.70, 0.80, hours_ago(1)),
            ("rss", "news_article", "economy", "JM",
             "Jamaica GDP Growth Revised to 2.8%", "IMF cites strong tourism recovery", 0.75, 0.45, 0.60, hours_ago(3)),
            ("rss", "news_article", "politics", "TT",
             "Trinidad Opposition Calls for Early Elections", "UNC demands elections citing mismanagement", -0.30, 0.55, 0.65, hours_ago(6)),
            ("rss", "news_article", "healthcare", "JM",
             "Jamaica Hospital Funding Crisis Deepens", "Kingston Public Hospital 40% staff shortage", -0.65, 0.82, 0.88, hours_ago(4)),
            ("rss", "news_article", "finance", "JM",
             "Jamaica Stock Exchange Hits 3-Month High", "JSE main index up 2.3%", 0.80, 0.35, 0.50, hours_ago(7)),
            ("rss", "news_article", "climate", "BB",
             "Barbados PM Pushes Climate Finance at UN", "Mottley advocates loss and damage fund", 0.45, 0.50, 0.65, hours_ago(14)),
            ("usgs", "earthquake", "climate", "",
             "M5.2 Earthquake - Caribbean Sea", "Moderate earthquake 120km south of Jamaica", -0.50, 0.58, 0.60, hours_ago(20)),
            ("rss", "news_article", "crime", "TT",
             "Trinidad Records Spike in Violent Crime", "15% increase this quarter", -0.70, 0.75, 0.80, hours_ago(9)),
            ("scrapling", "page_content_changed", "politics", "JM",
             "Trade Union Congress Removes JLP Endorsement", "Possible shift toward PNP", 0.20, 0.88, 0.92, hours_ago(1.5)),
            ("rss", "news_article", "politics", "JM",
             "PNP Announces Free Healthcare for Seniors", "Official commitment to free hospital visits over 65", 0.60, 0.85, 0.90, hours_ago(0.5)),
            ("finnhub", "market_news", "finance", "US",
             "Fed Signals Possible Rate Cut in Q3", "Markets rally on dovish language", 0.70, 0.60, 0.55, hours_ago(3)),
        ][:16]:
            sig = Signal(source=src, signal_type=stype, category=cat, country_code=cc, title=title,
                         summary=summary, sentiment_score=sent, anomaly_score=anom, importance=imp,
                         timestamp=ts, raw_data_json={"source_url": f"https://example.com/{stype}"})
            db.add(sig)
            signal_objs.append(sig)
        db.flush()

        # Chaos Index (7 days)
        for d in range(7, -1, -1):
            base = 55 + random.uniform(-10, 15)
            db.add(ChaosIndex(
                timestamp=days_ago(d), global_score=round(base, 1),
                category_scores_json={
                    "finance": round(base + random.uniform(-15, 15), 1),
                    "geopolitical": round(base + random.uniform(-10, 20), 1),
                    "supply_chain": round(base + random.uniform(-20, 10), 1),
                    "cyber": round(base + random.uniform(-25, 5), 1),
                    "climate": round(base + random.uniform(-15, 10), 1),
                },
                contributing_signal_ids_json=[s.id for s in random.sample(signal_objs, min(5, len(signal_objs)))],
            ))

        # Simulations
        db.add(Simulation(
            signal_ids_json=[signal_objs[0].id, signal_objs[3].id, signal_objs[5].id],
            status="completed", scenario_text="PNP healthcare policy voter impact simulation",
            report_json={
                "overall_sentiment": 0.62,
                "key_findings": ["62% positive voter reaction", "Strongest support among seniors (78%)", "34% raised funding concerns"],
                "tipping_points": ["JLP counter within 48hrs drops sentiment to 45%"],
                "recommendations": ["Release budget numbers with announcement", "Schedule Shadow Health Minister media tour"],
            },
            created_at=hours_ago(6), completed_at=hours_ago(5),
        ))
        db.add(Simulation(
            signal_ids_json=[signal_objs[7].id], status="running",
            scenario_text="Hospital funding crisis impact on healthcare debate",
            created_at=hours_ago(1),
        ))

        # Alerts
        for sig_id, msg in [
            (signal_objs[0].id, "High anomaly: PNP healthcare update (0.78)"),
            (signal_objs[8].id, "Critical: Hospital funding crisis (0.82)"),
            (signal_objs[13].id, "Critical: Trade Union removed JLP endorsement (0.88)"),
            (signal_objs[14].id, "Critical: PNP healthcare announcement (0.85)"),
        ]:
            db.add(Alert(signal_id=sig_id, alert_type="anomaly_threshold", severity="high",
                         message=msg, delivered_to_json={"channels": ["slack"]},
                         delivered_at=hours_ago(random.uniform(0, 6))))

        db.commit()
        print("=" * 60)
        print("  ORACLEFLOW DATA SEEDED IN MIROFISH")
        print("=" * 60)
        print(f"  Sites:       5")
        print(f"  Pages:       8")
        print(f"  Entities:    11")
        print(f"  Signals:     16")
        print(f"  Chaos Index: 8 (7 days)")
        print(f"  Simulations: 2")
        print(f"  Alerts:      4")
        print("=" * 60)


if __name__ == "__main__":
    seed()
