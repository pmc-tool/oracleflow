"""OracleFlow data feed fetchers — replace WorldMonitor with free public APIs."""

from app.oracleflow.feeds.rss import fetch_country_rss
from app.oracleflow.feeds.usgs import fetch_earthquakes
from app.oracleflow.feeds.finnhub import fetch_market_news
from app.oracleflow.feeds.acled import fetch_conflicts
from app.oracleflow.feeds.nasa import fetch_wildfires
from app.oracleflow.feeds.displacement import get_displacement_data
from app.oracleflow.feeds.clinicaltrials import fetch_clinical_trials
from app.oracleflow.feeds.otx import fetch_otx_pulses
from app.oracleflow.feeds.usda_fas import fetch_usda_fas
from app.oracleflow.feeds.open_fda import fetch_open_fda
from app.oracleflow.feeds.schemas import FeedArticle

__all__ = [
    "fetch_country_rss",
    "fetch_earthquakes",
    "fetch_market_news",
    "fetch_conflicts",
    "fetch_wildfires",
    "get_displacement_data",
    "fetch_clinical_trials",
    "fetch_otx_pulses",
    "fetch_usda_fas",
    "fetch_open_fda",
    "FeedArticle",
]
