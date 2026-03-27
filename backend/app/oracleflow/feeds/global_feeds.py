"""Global RSS feed configuration — curated from 200+ sources across categories."""

# Each feed: (url, category, name)
# Categories match our SignalCategory enum values

GLOBAL_FEEDS = [
    # === MAJOR NEWS (global) ===
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

    # === FINANCE & MARKETS ===
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "finance", "CNBC"),
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "finance", "MarketWatch"),
    ("https://finance.yahoo.com/news/rssindex", "finance", "Yahoo Finance"),
    ("https://seekingalpha.com/market_currents.xml", "finance", "Seeking Alpha"),

    # === POLITICS & GEOPOLITICS ===
    ("https://www.politico.com/rss/politicopicks.xml", "politics", "Politico"),
    ("https://rss.politico.com/politics-news.xml", "politics", "Politico Politics"),
    ("https://foreignpolicy.com/feed/", "geopolitical", "Foreign Policy"),
    ("https://www.cfr.org/rss.xml", "geopolitical", "CFR"),
    ("https://www.brookings.edu/feed/", "geopolitical", "Brookings"),
    ("https://www.atlanticcouncil.org/feed/", "geopolitical", "Atlantic Council"),
    ("https://www.csis.org/analysis/feed", "geopolitical", "CSIS"),
    ("https://thediplomat.com/feed/", "geopolitical", "The Diplomat"),

    # === GOVERNMENT ===
    ("https://www.whitehouse.gov/feed/", "politics", "White House"),
    ("https://www.state.gov/rss-feed/press-releases/feed/", "geopolitical", "State Dept"),
    ("https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945", "geopolitical", "Pentagon"),
    ("https://www.gov.uk/search/news-and-communications.atom", "politics", "UK Gov"),

    # === CYBERSECURITY ===
    ("https://krebsonsecurity.com/feed/", "cyber", "Krebs on Security"),
    ("https://www.darkreading.com/rss.xml", "cyber", "Dark Reading"),
    ("https://www.schneier.com/feed/atom/", "cyber", "Schneier"),
    ("https://www.cisa.gov/cybersecurity-advisories.xml", "cyber", "CISA Advisories"),
    ("https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml", "cyber", "NVD CVEs"),
    ("https://github.com/advisories.atom", "cyber", "GitHub Security Advisories"),
    ("https://msrc.microsoft.com/blog/feed", "cyber", "Microsoft Security Response"),
    ("https://www.us-cert.gov/ncas/alerts.xml", "cyber", "US-CERT Alerts"),
    ("https://feeds.feedburner.com/TheHackersNews", "cyber", "The Hacker News"),
    ("https://blog.talosintelligence.com/feeds/posts/default", "cyber", "Cisco Talos"),
    ("https://unit42.paloaltonetworks.com/feed/", "cyber", "Palo Alto Unit42"),

    # === CLIMATE & ENVIRONMENT ===
    ("https://climate.nasa.gov/news/rss.xml", "climate", "NASA Climate"),
    ("https://www.carbonbrief.org/feed/", "climate", "Carbon Brief"),

    # === DEFENSE & MILITARY ===
    ("https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Defense News"),
    ("https://www.militarytimes.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Military Times"),
    ("https://news.usni.org/feed", "geopolitical", "USNI News"),

    # === TECHNOLOGY ===
    ("https://feeds.arstechnica.com/arstechnica/index", "technology", "Ars Technica"),
    ("https://www.theverge.com/rss/index.xml", "technology", "The Verge"),
    ("https://techcrunch.com/feed/", "technology", "TechCrunch"),

    # === HEALTH ===
    ("https://tools.cdc.gov/api/v2/resources/media/403702.rss", "healthcare", "CDC"),
    ("https://www.who.int/feeds/entity/csr/don/en/rss.xml", "healthcare", "WHO Alerts"),

    # === ECONOMICS ===
    ("https://www.axios.com/feeds/feed.rss", "economy", "Axios"),

    # === CARIBBEAN SPECIFIC ===
    ("https://www.jamaicaobserver.com/feed/", "politics", "Jamaica Observer"),
    ("https://jamaica-gleaner.com/feed/rss.xml", "politics", "Jamaica Gleaner"),
    ("https://www.loopjamaica.com/rss.xml", "politics", "Loop Jamaica"),
    ("https://newsday.co.tt/feed/", "politics", "Trinidad Newsday"),
    ("https://www.guardian.co.tt/feed/", "politics", "Trinidad Guardian"),
    ("https://barbadostoday.bb/feed/", "politics", "Barbados Today"),

    # === SUPPLY CHAIN ===
    ("https://www.freightwaves.com/news/feed", "supply_chain", "FreightWaves"),
    ("https://www.supplychaindive.com/feeds/news/", "supply_chain", "Supply Chain Dive"),
    ("https://www.logisticsmgmt.com/rss", "supply_chain", "Logistics Management"),
    ("https://lloydslist.maritimeintelligence.informa.com/rss", "supply_chain", "Lloyd's List"),
    ("https://theloadstar.com/feed/", "supply_chain", "The Loadstar"),
    ("https://www.joc.com/rss/xml", "supply_chain", "Journal of Commerce"),
    ("https://splash247.com/feed/", "supply_chain", "Splash247"),
    ("https://www.seatrade-maritime.com/rss.xml", "supply_chain", "Seatrade Maritime"),
    ("https://www.hellenicshippingnews.com/feed/", "supply_chain", "Hellenic Shipping"),
    ("https://www.porttechnology.org/feed/", "supply_chain", "Port Technology"),

    # === DISASTER / NATURAL EVENTS ===
    ("https://www.fema.gov/feeds/disasters/rss.xml", "climate", "FEMA"),

    # === HUMANITARIAN / CRISIS ===
    ("https://www.gdacs.org/xml/rss.xml", "climate", "GDACS"),
    ("https://reliefweb.int/updates/rss.xml", "geopolitical", "ReliefWeb"),
    ("https://www.unhcr.org/rss/news.xml", "geopolitical", "UNHCR News"),
    ("https://www.icrc.org/en/rss", "geopolitical", "ICRC"),
    ("https://www.devex.com/news/rss", "economy", "Devex"),
    ("https://fews.net/rss.xml", "climate", "FEWS NET Famine Early Warning"),
    ("https://www.internal-displacement.org/rss.xml", "geopolitical", "IDMC Displacement"),
    ("https://www.preventionweb.net/rss", "climate", "PreventionWeb"),

    # === SUPPLY CHAIN - COMMODITIES & TRADE ===
    ("https://www.argusmedia.com/en/rss", "supply_chain", "Argus Media"),
    ("https://www.spglobal.com/commodityinsights/en/rss", "supply_chain", "S&P Global Commodity"),
    ("https://www.foodnavigator.com/rss", "supply_chain", "FoodNavigator"),
    ("https://www.semiconductorengineering.com/feed/", "supply_chain", "Semiconductor Engineering"),
    ("https://www.eetimes.com/feed/", "technology", "EE Times Semiconductors"),

    # =========================================================================
    # SPRINT 9 EXPANSION — ~150 new feeds from WorldMonitor domain list
    # =========================================================================

    # === MORE GLOBAL NEWS (~30) ===
    ("https://asia.nikkei.com/rss", "geopolitical", "Nikkei Asia"),
    ("https://www.scmp.com/rss/91/feed", "geopolitical", "South China Morning Post"),
    ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "geopolitical", "Times of India"),
    ("https://rss.dw.com/rdf/rss-en-all", "geopolitical", "Deutsche Welle"),
    ("https://www.france24.com/en/rss", "geopolitical", "France 24"),
    ("https://www3.nhk.or.jp/nhkworld/en/news/feeds/", "geopolitical", "NHK World"),
    ("https://www.abc.net.au/news/feed/51120/rss.xml", "geopolitical", "ABC Australia"),
    ("https://www.cbc.ca/cmlink/rss-world", "geopolitical", "CBC World"),
    ("https://www.rtbf.be/rss/section/info", "geopolitical", "RTBF"),
    ("https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada", "geopolitical", "El Pais"),
    ("https://xml2.corriereobjects.it/rss/english.xml", "geopolitical", "Corriere della Sera"),
    ("https://www.lemonde.fr/en/rss/une.xml", "geopolitical", "Le Monde"),
    ("https://www.euronews.com/rss", "geopolitical", "Euronews"),
    ("https://kyivindependent.com/feed/", "geopolitical", "Kyiv Independent"),
    ("https://www.themoscowtimes.com/rss/news", "geopolitical", "Moscow Times"),
    ("https://www.timesofisrael.com/feed/", "geopolitical", "Times of Israel"),
    ("https://www.haaretz.com/cmlink/1.628765", "geopolitical", "Haaretz"),
    ("https://english.alarabiya.net/tools/rss", "geopolitical", "Al Arabiya"),
    ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "geopolitical", "Channel NewsAsia"),
    ("https://japantoday.com/feed", "geopolitical", "Japan Today"),
    ("https://www.thehindu.com/news/international/feeder/default.rss", "geopolitical", "The Hindu"),
    ("https://indianexpress.com/section/world/feed/", "geopolitical", "Indian Express"),
    ("https://www.bangkokpost.com/rss/data/topstories.xml", "geopolitical", "Bangkok Post"),
    ("https://vnexpress.net/rss/tin-moi-nhat.rss", "geopolitical", "VnExpress"),
    ("https://feeds.abcnews.com/abcnews/internationalheadlines", "geopolitical", "ABC News Intl"),
    ("https://feeds.nbcnews.com/nbcnews/public/world", "geopolitical", "NBC News World"),
    ("https://www.cbsnews.com/latest/rss/world", "geopolitical", "CBS News World"),
    ("https://thehill.com/feed/", "politics", "The Hill"),
    ("https://www.pbs.org/newshour/feeds/rss/world", "geopolitical", "PBS NewsHour World"),
    ("https://www.spiegel.de/international/index.rss", "geopolitical", "Der Spiegel Intl"),
    ("https://meduza.io/rss/en/all", "geopolitical", "Meduza"),

    # === DEFENSE & MILITARY (~15) ===
    ("https://breakingdefense.com/feed/", "geopolitical", "Breaking Defense"),
    ("https://www.naval-technology.com/feed/", "geopolitical", "Naval Technology"),
    ("https://www.airforcemag.com/feed/", "geopolitical", "Air & Space Forces Magazine"),
    ("https://www.armytimes.com/arc/outboundfeeds/rss/?outputType=xml", "geopolitical", "Army Times"),
    ("https://nationalinterest.org/feed", "geopolitical", "National Interest"),
    ("https://warontherocks.com/feed/", "geopolitical", "War on the Rocks"),
    ("https://www.janes.com/feeds/news", "geopolitical", "Janes"),
    ("https://taskandpurpose.com/feed/", "geopolitical", "Task & Purpose"),
    ("https://www.twz.com/feed", "geopolitical", "The War Zone"),
    ("https://www.defenseone.com/rss/", "geopolitical", "Defense One"),
    ("https://www.oryxspioenkop.com/feeds/posts/default?alt=rss", "geopolitical", "Oryx"),
    ("https://gcaptain.com/feed/", "supply_chain", "gCaptain"),
    ("https://www.flightglobal.com/feed", "geopolitical", "FlightGlobal"),
    ("https://www.aviationweek.com/feed", "geopolitical", "Aviation Week"),
    ("https://rusi.org/feed", "geopolitical", "RUSI"),

    # === THINK TANKS & POLICY (~15) ===
    ("https://www.rand.org/pubs/feed.xml", "geopolitical", "RAND Corporation"),
    ("https://carnegieendowment.org/rss/solr.xml", "geopolitical", "Carnegie Endowment"),
    ("https://www.chathamhouse.org/feed", "geopolitical", "Chatham House"),
    ("https://www.heritage.org/rss/all-research.xml", "politics", "Heritage Foundation"),
    ("https://www.iiss.org/feed", "geopolitical", "IISS"),
    ("https://www.crisisgroup.org/feed", "geopolitical", "Crisis Group"),
    ("https://www.wilsoncenter.org/feed", "geopolitical", "Wilson Center"),
    ("https://www.stimson.org/feed/", "geopolitical", "Stimson Center"),
    ("https://www.cnas.org/feed", "geopolitical", "CNAS"),
    ("https://www.foreignaffairs.com/rss.xml", "geopolitical", "Foreign Affairs"),
    ("https://responsiblestatecraft.org/feed/", "geopolitical", "Responsible Statecraft"),
    ("https://www.fpri.org/feed/", "geopolitical", "FPRI"),
    ("https://jamestown.org/feed/", "geopolitical", "Jamestown Foundation"),
    ("https://ecfr.eu/feed/", "geopolitical", "ECFR"),
    ("https://www.gmfus.org/feed", "geopolitical", "German Marshall Fund"),
    ("https://www.lowyinstitute.org/feed", "geopolitical", "Lowy Institute"),
    ("https://www.mei.edu/feed", "geopolitical", "MEI"),
    ("https://fas.org/feed/", "geopolitical", "Federation of American Scientists"),
    ("https://www.armscontrol.org/rss.xml", "geopolitical", "Arms Control Association"),
    ("https://thebulletin.org/feed/", "geopolitical", "Bulletin of the Atomic Scientists"),

    # === CYBERSECURITY (~10) ===
    ("https://www.bleepingcomputer.com/feed/", "cyber", "BleepingComputer"),
    ("https://therecord.media/feed", "cyber", "The Record"),
    ("https://www.securityweek.com/feed/", "cyber", "SecurityWeek"),
    ("https://threatpost.com/feed/", "cyber", "Threatpost"),
    ("https://www.cyberscoop.com/feed/", "cyber", "CyberScoop"),
    ("https://www.cisa.gov/news.xml", "cyber", "CISA"),
    ("https://www.ransomware.live/rss.xml", "cyber", "Ransomware.live"),
    ("https://www.dhs.gov/news-releases/rss.xml", "cyber", "DHS"),
    ("https://www.bellingcat.com/feed/", "cyber", "Bellingcat"),
    ("https://insightcrime.org/feed/", "crime", "InSight Crime"),

    # === SCIENCE & CLIMATE (~10) ===
    ("https://www.nature.com/nature.rss", "technology", "Nature"),
    ("https://www.sciencedaily.com/rss/all.xml", "technology", "ScienceDaily"),
    ("https://phys.org/rss-feed/", "technology", "Phys.org"),
    ("https://www.climatechangenews.com/feed/", "climate", "Climate Home News"),
    ("https://insideclimatenews.org/feed/", "climate", "Inside Climate News"),
    ("https://www.livescience.com/feeds/all", "technology", "Live Science"),
    ("https://www.newscientist.com/feed/home/", "technology", "New Scientist"),
    ("https://news.mongabay.com/feed/", "climate", "Mongabay"),
    ("https://news.mit.edu/rss/feed", "technology", "MIT News"),
    ("https://singularityhub.com/feed/", "technology", "Singularity Hub"),

    # === ECONOMIC (~10) ===
    ("https://www.economist.com/finance-and-economics/rss.xml", "economy", "The Economist"),
    ("https://www.ft.com/rss/home", "economy", "Financial Times"),
    ("https://feeds.content.dowjones.io/public/rss/mw_topstories", "economy", "WSJ via Dow Jones"),
    ("https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline", "finance", "Investopedia"),
    ("https://www.barrons.com/feed", "finance", "Barrons"),
    ("https://www.kitco.com/rss/gold.xml", "finance", "Kitco Gold"),
    ("https://oilprice.com/rss/main", "economy", "OilPrice"),
    ("https://www.imf.org/en/News/Rss?type=all", "economy", "IMF News"),
    ("https://news.crunchbase.com/feed/", "economy", "Crunchbase News"),
    ("https://www.federalreserve.gov/feeds/press_all.xml", "economy", "Federal Reserve"),
    ("https://home.treasury.gov/system/files/276/rss.xml", "economy", "US Treasury"),
    ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&dateb=&owner=include&count=40&search_text=&action=getcompany", "finance", "SEC 8-K Filings"),
    ("https://www.ecb.europa.eu/rss/press.html", "economy", "ECB Press"),
    ("https://www.bis.org/rss/presses.rss", "economy", "BIS Press"),

    # === CARIBBEAN & LATIN AMERICA (~10) ===
    ("https://www.jamaicagleaner.com/feed/", "politics", "Jamaica Gleaner Alt"),
    ("https://trinidadexpress.com/search/?f=rss", "politics", "Trinidad Express"),
    ("https://www.miamiherald.com/news/nation-world/world/americas/feed/", "geopolitical", "Miami Herald Americas"),
    ("https://mercopress.com/rss", "geopolitical", "MercoPress"),
    ("https://www.batimes.com.ar/feed", "geopolitical", "Buenos Aires Times"),
    ("https://www.infobae.com/feeds/rss/", "geopolitical", "Infobae"),
    ("https://www.clarin.com/rss/lo-ultimo/", "geopolitical", "Clarin"),
    ("https://oglobo.globo.com/rss.xml", "geopolitical", "O Globo"),
    ("https://feeds.folha.uol.com.br/world/rss091.xml", "geopolitical", "Folha de S.Paulo"),
    ("https://mexiconewsdaily.com/feed/", "geopolitical", "Mexico News Daily"),
    ("https://www.eltiempo.com/rss/el_tiempo.xml", "geopolitical", "El Tiempo"),
    ("https://www.eluniversal.com.mx/rss.xml", "geopolitical", "El Universal Mexico"),

    # === AFRICA (~10) ===
    ("https://www.africanews.com/feed/", "geopolitical", "Africanews"),
    ("https://feeds.news24.com/articles/news24/TopStories/rss", "geopolitical", "News24 South Africa"),
    ("https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "geopolitical", "AllAfrica"),
    ("https://www.theafricareport.com/feed/", "geopolitical", "The Africa Report"),
    ("https://www.premiumtimesng.com/feed", "geopolitical", "Premium Times Nigeria"),
    ("https://www.vanguardngr.com/feed/", "geopolitical", "Vanguard Nigeria"),
    ("https://dailytrust.com/feed/", "geopolitical", "Daily Trust Nigeria"),
    ("https://www.jeuneafrique.com/feed/", "geopolitical", "Jeune Afrique"),
    ("https://techcabal.com/feed/", "technology", "TechCabal Africa"),
    ("https://disrupt-africa.com/feed/", "technology", "Disrupt Africa"),

    # === MIDDLE EAST ===
    ("https://www.omanobserver.om/feed/", "geopolitical", "Oman Observer"),
    ("https://www.lorientlejour.com/feed", "geopolitical", "L'Orient Le Jour"),
    ("https://www.mei.edu/feed", "geopolitical", "Middle East Institute"),

    # === TECHNOLOGY EXPANDED ===
    ("https://www.technologyreview.com/feed/", "technology", "MIT Technology Review"),
    ("https://venturebeat.com/feed/", "technology", "VentureBeat"),
    ("https://www.techmeme.com/feed.xml", "technology", "Techmeme"),
    ("https://www.engadget.com/rss.xml", "technology", "Engadget"),
    ("https://feed.infoq.com/", "technology", "InfoQ"),
    ("https://thenewstack.io/feed/", "technology", "The New Stack"),
    ("https://github.blog/feed/", "technology", "GitHub Blog"),
    ("https://www.tomshardware.com/feeds/all", "technology", "Tom's Hardware"),
    ("https://www.producthunt.com/feed", "technology", "Product Hunt"),
    ("https://www.techinasia.com/feed", "technology", "Tech in Asia"),
    ("https://dev.to/feed/", "technology", "DEV Community"),

    # === CRYPTO & BLOCKCHAIN ===
    ("https://www.coindesk.com/arc/outboundfeeds/rss/", "finance", "CoinDesk"),
    ("https://cointelegraph.com/rss", "finance", "Cointelegraph"),
    ("https://decrypt.co/feed", "finance", "Decrypt"),
    ("https://blockworks.co/feed", "finance", "Blockworks"),
    ("https://bitcoinmagazine.com/.rss/full/", "finance", "Bitcoin Magazine"),

    # === COMMODITIES & ENERGY ===
    ("https://www.mining.com/feed/", "economy", "Mining.com"),
    ("https://www.rigzone.com/news/rss/rigzone_latest.aspx", "economy", "Rigzone"),
    ("https://www.eia.gov/rss/todayinenergy.xml", "economy", "EIA"),
    ("https://www.miningweekly.com/feed", "economy", "Mining Weekly"),
    ("https://www.mining-technology.com/feed/", "economy", "Mining Technology"),

    # === AVIATION ===
    ("https://simpleflying.com/feed/", "technology", "Simple Flying"),
    ("https://airlinegeeks.com/feed/", "technology", "Airline Geeks"),
    ("https://www.aviationpros.com/rss", "technology", "AviationPros"),

    # === UN & INTERNATIONAL ORGANIZATIONS ===
    ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "geopolitical", "UN News"),
    ("https://www.iaea.org/feeds/news", "geopolitical", "IAEA"),
    ("https://www.fao.org/news/rss.xml", "climate", "FAO News"),

    # === EUROPEAN NEWS ===
    ("https://feeds.nos.nl/nosnieuwsalgemeen", "geopolitical", "NOS Netherlands"),
    ("https://www.svt.se/nyheter/rss.xml", "geopolitical", "SVT Sweden"),
    ("https://tvn24.pl/najnowsze.xml", "geopolitical", "TVN24 Poland"),
    ("https://www.hurriyet.com.tr/rss/english", "geopolitical", "Hurriyet Turkey"),

    # === HEALTH EXPANDED ===
    ("https://www.ecdc.europa.eu/en/feed", "healthcare", "ECDC"),
    ("https://www.afro.who.int/rss.xml", "healthcare", "WHO Africa"),

    # === POSITIVE NEWS ===
    ("https://www.goodnewsnetwork.org/feed/", "other", "Good News Network"),
    ("https://www.positive.news/feed/", "other", "Positive News"),

    # === STARTUP & VC ===
    ("https://a16z.com/feed/", "economy", "Andreessen Horowitz"),
    ("https://www.eu-startups.com/feed/", "economy", "EU-Startups"),
    ("https://sifted.eu/feed/", "economy", "Sifted"),
    ("https://inc42.com/feed/", "economy", "Inc42 India"),

    # === MISSING CRITICAL FEEDS (customer-requested) ===
    ("https://www.opec.org/opec_web/en/press_room/28.htm", "economy", "OPEC News"),
    ("https://www.cftc.gov/Newsroom/rss_feed.html", "finance", "CFTC"),
    ("https://ofac.treasury.gov/recent-actions", "geopolitical", "OFAC Sanctions"),
    ("https://www.iea.org/rss", "economy", "IEA"),
    ("https://www.eia.gov/rss/", "economy", "EIA Main"),
    ("https://alerts.weather.gov/cap/us.php?x=0", "climate", "NOAA Weather Alerts"),
    ("https://www.nhc.noaa.gov/index-at.xml", "climate", "NHC Atlantic Hurricane"),
    ("https://www.nhc.noaa.gov/index-ep.xml", "climate", "NHC East Pacific Hurricane"),
    ("https://googleprojectzero.blogspot.com/feeds/posts/default", "cyber", "Google Project Zero"),
]

# Total: 236 feeds across 12+ categories (includes humanitarian, supply chain, regulatory & weather packs)
# Expandable — add more by appending to list
