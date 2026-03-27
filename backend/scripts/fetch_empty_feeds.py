#!/usr/bin/env python3
"""Fetch signals ONLY from feeds that currently have 0 signals in the database.

Targets the newly added feeds (FDA, biotech, GDACS, NVD, agriculture, etc.)
that haven't been ingested yet.
"""

import json
import re
import sys
import socket
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text

# Set global socket timeout to prevent hanging on slow feeds
socket.setdefaulttimeout(8)

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"

# All known feeds — (url, category, name)
# Copied from global_feeds.py
ALL_FEEDS = [
    ("https://feeds.bbci.co.uk/news/world/rss.xml", "geopolitical", "BBC World"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml", "economy", "BBC Business"),
    ("https://feeds.bbci.co.uk/news/politics/rss.xml", "politics", "BBC Politics"),
    ("https://feeds.bbci.co.uk/news/health/rss.xml", "healthcare", "BBC Health"),
    ("https://feeds.bbci.co.uk/news/technology/rss.xml", "technology", "BBC Tech"),
    ("https://rss.cnn.com/rss/edition_world.rss", "geopolitical", "CNN World"),
    ("https://rss.cnn.com/rss/money_news_international.rss", "finance", "CNN Money"),
    ("https://feeds.reuters.com/Reuters/worldNews", "geopolitical", "Reuters World"),
    ("https://feeds.reuters.com/reuters/businessNews", "finance", "Reuters Business"),
    ("https://feeds.npr.org/1004/rss.xml", "geopolitical", "NPR World"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "geopolitical", "Al Jazeera"),
    ("https://www.theguardian.com/world/rss", "geopolitical", "Guardian World"),
    ("https://www.theguardian.com/politics/rss", "politics", "Guardian Politics"),
    ("https://www.theguardian.com/environment/climate-crisis/rss", "climate", "Guardian Climate"),
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "finance", "CNBC"),
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "finance", "MarketWatch"),
    ("https://finance.yahoo.com/news/rssindex", "finance", "Yahoo Finance"),
    ("https://seekingalpha.com/market_currents.xml", "finance", "Seeking Alpha"),
    ("https://www.politico.com/rss/politicopicks.xml", "politics", "Politico"),
    ("https://foreignpolicy.com/feed/", "geopolitical", "Foreign Policy"),
    ("https://www.cfr.org/rss.xml", "geopolitical", "CFR"),
    ("https://www.brookings.edu/feed/", "geopolitical", "Brookings"),
    ("https://www.atlanticcouncil.org/feed/", "geopolitical", "Atlantic Council"),
    ("https://www.csis.org/analysis/feed", "geopolitical", "CSIS"),
    ("https://thediplomat.com/feed/", "geopolitical", "The Diplomat"),
    ("https://www.whitehouse.gov/feed/", "politics", "White House"),
    ("https://www.state.gov/rss-feed/press-releases/feed/", "geopolitical", "State Dept"),
    ("https://krebsonsecurity.com/feed/", "cyber", "Krebs on Security"),
    ("https://www.darkreading.com/rss.xml", "cyber", "Dark Reading"),
    ("https://www.schneier.com/feed/atom/", "cyber", "Schneier"),
    ("https://www.cisa.gov/cybersecurity-advisories.xml", "cyber", "CISA Advisories"),
    ("https://github.com/advisories.atom", "cyber", "GitHub Security Advisories"),
    ("https://msrc.microsoft.com/blog/feed", "cyber", "Microsoft Security Response"),
    ("https://feeds.feedburner.com/TheHackersNews", "cyber", "The Hacker News"),
    ("https://blog.talosintelligence.com/feeds/posts/default", "cyber", "Cisco Talos"),
    ("https://unit42.paloaltonetworks.com/feed/", "cyber", "Palo Alto Unit42"),
    ("https://climate.nasa.gov/news/rss.xml", "climate", "NASA Climate"),
    ("https://www.carbonbrief.org/feed/", "climate", "Carbon Brief"),
    ("https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Defense News"),
    ("https://www.militarytimes.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Military Times"),
    ("https://news.usni.org/feed", "geopolitical", "USNI News"),
    ("https://feeds.arstechnica.com/arstechnica/index", "technology", "Ars Technica"),
    ("https://www.theverge.com/rss/index.xml", "technology", "The Verge"),
    ("https://techcrunch.com/feed/", "technology", "TechCrunch"),
    ("https://tools.cdc.gov/api/v2/resources/media/403702.rss", "healthcare", "CDC"),
    ("https://www.who.int/feeds/entity/csr/don/en/rss.xml", "healthcare", "WHO Alerts"),
    ("https://www.axios.com/feeds/feed.rss", "economy", "Axios"),
    ("https://www.jamaicaobserver.com/feed/", "politics", "Jamaica Observer"),
    ("https://www.loopjamaica.com/rss.xml", "politics", "Loop Jamaica"),
    ("https://newsday.co.tt/feed/", "politics", "Trinidad Newsday"),
    ("https://www.guardian.co.tt/feed/", "politics", "Trinidad Guardian"),
    ("https://barbadostoday.bb/feed/", "politics", "Barbados Today"),
    ("https://www.freightwaves.com/news/feed", "supply_chain", "FreightWaves"),
    ("https://www.supplychaindive.com/feeds/news/", "supply_chain", "Supply Chain Dive"),
    ("https://theloadstar.com/feed/", "supply_chain", "The Loadstar"),
    ("https://splash247.com/feed/", "supply_chain", "Splash247"),
    ("https://www.seatrade-maritime.com/rss.xml", "supply_chain", "Seatrade Maritime"),
    ("https://www.hellenicshippingnews.com/feed/", "supply_chain", "Hellenic Shipping"),
    ("https://www.porttechnology.org/feed/", "supply_chain", "Port Technology"),
    ("https://www.fema.gov/feeds/disasters/rss.xml", "climate", "FEMA"),
    ("https://www.gdacs.org/xml/rss.xml", "climate", "GDACS"),
    ("https://reliefweb.int/updates/rss.xml", "geopolitical", "ReliefWeb"),
    ("https://www.unhcr.org/rss/news.xml", "geopolitical", "UNHCR News"),
    ("https://www.icrc.org/en/rss", "geopolitical", "ICRC"),
    ("https://www.devex.com/news/rss", "economy", "Devex"),
    ("https://www.foodnavigator.com/rss", "supply_chain", "FoodNavigator"),
    ("https://www.semiconductorengineering.com/feed/", "supply_chain", "Semiconductor Engineering"),
    ("https://asia.nikkei.com/rss", "geopolitical", "Nikkei Asia"),
    ("https://www.scmp.com/rss/91/feed", "geopolitical", "South China Morning Post"),
    ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "geopolitical", "Times of India"),
    ("https://rss.dw.com/rdf/rss-en-all", "geopolitical", "Deutsche Welle"),
    ("https://www.france24.com/en/rss", "geopolitical", "France 24"),
    ("https://www.abc.net.au/news/feed/51120/rss.xml", "geopolitical", "ABC Australia"),
    ("https://www.cbc.ca/cmlink/rss-world", "geopolitical", "CBC World"),
    ("https://kyivindependent.com/feed/", "geopolitical", "Kyiv Independent"),
    ("https://www.themoscowtimes.com/rss/news", "geopolitical", "Moscow Times"),
    ("https://www.timesofisrael.com/feed/", "geopolitical", "Times of Israel"),
    ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "geopolitical", "Channel NewsAsia"),
    ("https://japantoday.com/feed", "geopolitical", "Japan Today"),
    ("https://www.thehindu.com/news/international/feeder/default.rss", "geopolitical", "The Hindu"),
    ("https://indianexpress.com/section/world/feed/", "geopolitical", "Indian Express"),
    ("https://www.bangkokpost.com/rss/data/topstories.xml", "geopolitical", "Bangkok Post"),
    ("https://feeds.abcnews.com/abcnews/internationalheadlines", "geopolitical", "ABC News Intl"),
    ("https://feeds.nbcnews.com/nbcnews/public/world", "geopolitical", "NBC News World"),
    ("https://www.cbsnews.com/latest/rss/world", "geopolitical", "CBS News World"),
    ("https://thehill.com/feed/", "politics", "The Hill"),
    ("https://www.pbs.org/newshour/feeds/rss/world", "geopolitical", "PBS NewsHour World"),
    ("https://www.spiegel.de/international/index.rss", "geopolitical", "Der Spiegel Intl"),
    ("https://meduza.io/rss/en/all", "geopolitical", "Meduza"),
    ("https://breakingdefense.com/feed/", "geopolitical", "Breaking Defense"),
    ("https://www.naval-technology.com/feed/", "geopolitical", "Naval Technology"),
    ("https://www.airforcemag.com/feed/", "geopolitical", "Air & Space Forces Magazine"),
    ("https://www.armytimes.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Army Times"),
    ("https://nationalinterest.org/feed", "geopolitical", "National Interest"),
    ("https://warontherocks.com/feed/", "geopolitical", "War on the Rocks"),
    ("https://taskandpurpose.com/feed/", "geopolitical", "Task & Purpose"),
    ("https://www.defenseone.com/rss/", "geopolitical", "Defense One"),
    ("https://gcaptain.com/feed/", "supply_chain", "gCaptain"),
    ("https://www.rand.org/pubs/feed.xml", "geopolitical", "RAND Corporation"),
    ("https://carnegieendowment.org/rss/solr.xml", "geopolitical", "Carnegie Endowment"),
    ("https://www.crisisgroup.org/feed", "geopolitical", "Crisis Group"),
    ("https://www.foreignaffairs.com/rss.xml", "geopolitical", "Foreign Affairs"),
    ("https://responsiblestatecraft.org/feed/", "geopolitical", "Responsible Statecraft"),
    ("https://jamestown.org/feed/", "geopolitical", "Jamestown Foundation"),
    ("https://fas.org/feed/", "geopolitical", "Federation of American Scientists"),
    ("https://www.armscontrol.org/rss.xml", "geopolitical", "Arms Control Association"),
    ("https://thebulletin.org/feed/", "geopolitical", "Bulletin of the Atomic Scientists"),
    ("https://www.bleepingcomputer.com/feed/", "cyber", "BleepingComputer"),
    ("https://therecord.media/feed", "cyber", "The Record"),
    ("https://www.securityweek.com/feed/", "cyber", "SecurityWeek"),
    ("https://www.cyberscoop.com/feed/", "cyber", "CyberScoop"),
    ("https://www.cisa.gov/news.xml", "cyber", "CISA"),
    ("https://www.ransomware.live/rss.xml", "cyber", "Ransomware.live"),
    ("https://www.dhs.gov/news-releases/rss.xml", "cyber", "DHS"),
    ("https://www.bellingcat.com/feed/", "cyber", "Bellingcat"),
    ("https://insightcrime.org/feed/", "crime", "InSight Crime"),
    ("https://www.nature.com/nature.rss", "technology", "Nature"),
    ("https://www.sciencedaily.com/rss/all.xml", "technology", "ScienceDaily"),
    ("https://phys.org/rss-feed/", "technology", "Phys.org"),
    ("https://www.climatechangenews.com/feed/", "climate", "Climate Home News"),
    ("https://insideclimatenews.org/feed/", "climate", "Inside Climate News"),
    ("https://news.mongabay.com/feed/", "climate", "Mongabay"),
    ("https://news.mit.edu/rss/feed", "technology", "MIT News"),
    ("https://singularityhub.com/feed/", "technology", "Singularity Hub"),
    ("https://www.economist.com/finance-and-economics/rss.xml", "economy", "The Economist"),
    ("https://www.ft.com/rss/home", "economy", "Financial Times"),
    ("https://feeds.content.dowjones.io/public/rss/mw_topstories", "economy", "WSJ via Dow Jones"),
    ("https://www.kitco.com/rss/gold.xml", "finance", "Kitco Gold"),
    ("https://oilprice.com/rss/main", "economy", "OilPrice"),
    ("https://www.imf.org/en/News/Rss?type=all", "economy", "IMF News"),
    ("https://news.crunchbase.com/feed/", "economy", "Crunchbase News"),
    ("https://www.federalreserve.gov/feeds/press_all.xml", "economy", "Federal Reserve"),
    ("https://www.ecb.europa.eu/rss/press.html", "economy", "ECB Press"),
    ("https://www.africanews.com/feed/", "geopolitical", "Africanews"),
    ("https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "geopolitical", "AllAfrica"),
    ("https://www.theafricareport.com/feed/", "geopolitical", "The Africa Report"),
    ("https://www.premiumtimesng.com/feed", "geopolitical", "Premium Times Nigeria"),
    ("https://www.vanguardngr.com/feed/", "geopolitical", "Vanguard Nigeria"),
    ("https://dailytrust.com/feed/", "geopolitical", "Daily Trust Nigeria"),
    ("https://techcabal.com/feed/", "technology", "TechCabal Africa"),
    ("https://www.technologyreview.com/feed/", "technology", "MIT Technology Review"),
    ("https://venturebeat.com/feed/", "technology", "VentureBeat"),
    ("https://thenewstack.io/feed/", "technology", "The New Stack"),
    ("https://github.blog/feed/", "technology", "GitHub Blog"),
    ("https://www.coindesk.com/arc/outboundfeeds/rss/", "finance", "CoinDesk"),
    ("https://cointelegraph.com/rss", "finance", "Cointelegraph"),
    ("https://decrypt.co/feed", "finance", "Decrypt"),
    ("https://blockworks.co/feed", "finance", "Blockworks"),
    ("https://bitcoinmagazine.com/.rss/full/", "finance", "Bitcoin Magazine"),
    ("https://www.mining.com/feed/", "economy", "Mining.com"),
    ("https://www.eia.gov/rss/todayinenergy.xml", "economy", "EIA"),
    ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "geopolitical", "UN News"),
    ("https://www.iaea.org/feeds/news", "geopolitical", "IAEA"),
    ("https://www.fao.org/news/rss.xml", "climate", "FAO News"),
    ("https://www.ecdc.europa.eu/en/feed", "healthcare", "ECDC"),
    ("https://a16z.com/feed/", "economy", "Andreessen Horowitz"),
    # Healthcare / Biotech (new)
    ("https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/fda-newsroom/rss.xml", "healthcare", "FDA Newsroom"),
    ("https://www.statnews.com/feed/", "healthcare", "STAT News"),
    ("https://www.fiercebiotech.com/rss/xml", "healthcare", "FierceBiotech"),
    ("https://www.fiercepharma.com/rss/xml", "healthcare", "FiercePharma"),
    ("https://endpts.com/feed/", "healthcare", "Endpoints News"),
    ("https://www.biopharmadive.com/feeds/news/", "healthcare", "BioPharma Dive"),
    ("https://www.pharmaceutical-technology.com/feed/", "healthcare", "Pharmaceutical Technology"),
    # AI / Tech
    ("https://siliconangle.com/feed/", "technology", "SiliconANGLE"),
    ("https://hai.stanford.edu/news/rss.xml", "technology", "Stanford HAI"),
    # Maritime
    ("https://www.maritime-executive.com/rss", "supply_chain", "Maritime Executive"),
    # Macro economics
    ("https://voxeu.org/rss", "economy", "VoxEU CEPR"),
    # Agriculture
    ("https://www.usda.gov/rss/home.xml", "economy", "USDA"),
    ("https://www.ers.usda.gov/rss/latest-publications.xml", "economy", "USDA ERS"),
    ("https://www.agriculture.com/rss/news", "economy", "Agriculture.com"),
    # Weather
    ("https://alerts.weather.gov/cap/us.php?x=0", "climate", "NOAA Weather Alerts"),
    ("https://googleprojectzero.blogspot.com/feeds/posts/default", "cyber", "Google Project Zero"),
]


# ---------------------------------------------------------------------------
# Inline country guesser (simple version)
# ---------------------------------------------------------------------------
COUNTRY_HINTS = {
    "US": ["united states", "u.s.", "washington", "congress", "pentagon", "white house", "biden", "trump", "federal reserve"],
    "GB": ["united kingdom", "britain", "london", "downing street", "parliament"],
    "CN": ["china", "chinese", "beijing", "shanghai", "xi jinping"],
    "RU": ["russia", "russian", "moscow", "putin", "kremlin"],
    "UA": ["ukraine", "ukrainian", "kyiv", "zelensky"],
    "JP": ["japan", "japanese", "tokyo"],
    "DE": ["germany", "german", "berlin"],
    "FR": ["france", "french", "paris", "macron"],
    "IN": ["india", "indian", "delhi", "mumbai", "modi"],
    "IL": ["israel", "israeli", "netanyahu", "gaza"],
    "IR": ["iran", "iranian", "tehran"],
    "KR": ["south korea", "korean", "seoul"],
    "AU": ["australia", "australian", "canberra", "sydney"],
    "BR": ["brazil", "brazilian", "brasilia"],
    "CA": ["canada", "canadian", "ottawa", "toronto"],
    "SA": ["saudi arabia", "saudi", "riyadh"],
    "TR": ["turkey", "turkish", "ankara", "istanbul", "erdogan"],
    "EG": ["egypt", "egyptian", "cairo"],
    "NG": ["nigeria", "nigerian", "lagos", "abuja"],
    "ZA": ["south africa", "cape town", "johannesburg"],
    "MX": ["mexico", "mexican"],
    "IT": ["italy", "italian", "rome", "milan"],
    "ES": ["spain", "spanish", "madrid"],
    "PL": ["poland", "polish", "warsaw"],
    "NL": ["netherlands", "dutch", "amsterdam"],
    "PK": ["pakistan", "pakistani", "islamabad"],
    "AF": ["afghanistan", "afghan", "kabul", "taliban"],
    "SY": ["syria", "syrian", "damascus"],
    "YE": ["yemen", "yemeni", "houthi"],
    "SD": ["sudan", "sudanese", "khartoum", "darfur"],
    "MM": ["myanmar", "burma", "yangon"],
    "TW": ["taiwan", "taiwanese", "taipei"],
}


def guess_country(text_str: str) -> str:
    t = text_str.lower()
    scores = {}
    for code, keywords in COUNTRY_HINTS.items():
        hits = sum(1 for kw in keywords if kw in t)
        if hits > 0:
            scores[code] = hits
    if not scores:
        return ""
    return max(scores, key=scores.get)


def _estimate_anomaly(text_str: str) -> float:
    t = text_str.lower()
    high = ["breaking", "urgent", "crisis", "emergency", "war", "attack", "explosion", "killed",
            "critical", "zero-day", "ransomware", "breach"]
    med = ["threat", "sanction", "protest", "conflict", "earthquake", "flood", "hack", "vulnerability"]

    h = sum(1 for kw in high if kw in t)
    m = sum(1 for kw in med if kw in t)

    if h >= 2:
        return min(1.0, 0.85 + h * 0.05)
    elif h == 1:
        return 0.65 + m * 0.05
    elif m > 0:
        return 0.45 + m * 0.05
    return 0.25


def _estimate_sentiment(text_str: str) -> float:
    t = text_str.lower()
    neg = ["kill", "attack", "crash", "crisis", "war", "bomb", "death", "collapse",
           "threat", "sanction", "strike", "invasion", "earthquake", "flood",
           "ransomware", "breach", "hack", "explosion", "conflict", "famine"]
    pos = ["peace", "agreement", "growth", "recovery", "breakthrough", "ceasefire",
           "cooperation", "aid", "progress", "reform", "success"]
    n = sum(1 for kw in neg if kw in t)
    p = sum(1 for kw in pos if kw in t)
    if n + p == 0:
        return 0.0
    return round((p - n) / (p + n), 2)


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Get set of source_names already in DB
        existing_sources = set()
        rows = conn.execute(text(
            "SELECT DISTINCT raw_data_json->>'source_name' FROM signals "
            "WHERE raw_data_json->>'source_name' IS NOT NULL"
        )).fetchall()
        for r in rows:
            if r[0]:
                existing_sources.add(r[0])

        print(f"Existing feed sources in DB: {len(existing_sources)}")

        # Find feeds with 0 signals
        empty_feeds = [(url, cat, name) for url, cat, name in ALL_FEEDS if name not in existing_sources]
        print(f"Feeds with 0 signals: {len(empty_feeds)}")

        if not empty_feeds:
            print("All feeds already have signals. Nothing to do.")
            return

        total_inserted = 0
        feeds_attempted = 0
        feeds_succeeded = 0
        now = datetime.now(timezone.utc)

        for url, category, name in empty_feeds:
            feeds_attempted += 1
            try:
                feed = feedparser.parse(url)
                entries = feed.entries[:10]  # Max 10 per feed to be efficient

                if not entries:
                    continue

                count = 0
                for entry in entries:
                    title = (entry.get('title') or '').strip()
                    if not title or len(title) < 10:
                        continue

                    # Dedup check
                    existing = conn.execute(text(
                        "SELECT 1 FROM signals WHERE title = :title LIMIT 1"
                    ), {"title": title[:1024]}).scalar()
                    if existing:
                        continue

                    summary = (entry.get('summary') or entry.get('description') or '')[:500]
                    link = entry.get('link', '')
                    combined = title + " " + summary

                    country_code = guess_country(combined)
                    anomaly = round(_estimate_anomaly(combined), 4)
                    sentiment = _estimate_sentiment(combined)
                    importance = round(min(1.0, 0.5 + anomaly * 0.3), 2)

                    raw_data = json.dumps({
                        'link': link,
                        'source_name': name,
                    })

                    conn.execute(text(
                        "INSERT INTO signals (source, signal_type, category, country_code, "
                        "title, summary, raw_data_json, sentiment_score, anomaly_score, "
                        "importance, timestamp) "
                        "VALUES (:source, :stype, :cat, :cc, :title, :summary, "
                        ":raw, :sent, :anomaly, :imp, :ts)"
                    ), {
                        "source": "rss",
                        "stype": "feed_article",
                        "cat": category,
                        "cc": country_code,
                        "title": title[:1024],
                        "summary": summary,
                        "raw": raw_data,
                        "sent": sentiment,
                        "anomaly": anomaly,
                        "imp": importance,
                        "ts": now.isoformat(),
                    })
                    count += 1

                if count > 0:
                    conn.commit()
                    feeds_succeeded += 1
                    total_inserted += count
                    print(f"  [{feeds_attempted}/{len(empty_feeds)}] {name}: {count} signals")

            except Exception as e:
                print(f"  [{feeds_attempted}/{len(empty_feeds)}] {name}: ERROR - {str(e)[:80]}")
                try:
                    conn.rollback()
                except Exception:
                    pass

        print(f"\n=== Summary ===")
        print(f"Feeds attempted: {feeds_attempted}")
        print(f"Feeds with new signals: {feeds_succeeded}")
        print(f"Total signals inserted: {total_inserted}")

        total = conn.execute(text("SELECT COUNT(*) FROM signals")).scalar()
        print(f"Total signals in DB: {total}")


if __name__ == "__main__":
    main()
