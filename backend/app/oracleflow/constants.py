"""Enums and constants used across OracleFlow."""

from enum import Enum


class PageType(str, Enum):
    HOMEPAGE = "homepage"
    NEWS_INDEX = "news_index"
    ARTICLE = "article"
    POLICY_PAGE = "policy_page"
    TEAM_PAGE = "team_page"
    EVENTS = "events"
    FUNDRAISING = "fundraising"
    STATIC = "static"
    IGNORE = "ignore"
    UNKNOWN = "unknown"


class MonitoringFrequency(str, Enum):
    REALTIME = "5m"
    HIGH = "15m"
    MEDIUM = "30m"
    STANDARD = "2h"
    LOW = "6h"
    WEEKLY = "7d"
    DISABLED = "disabled"


# Map page types to default monitoring frequencies
PAGE_TYPE_FREQUENCY = {
    PageType.HOMEPAGE: MonitoringFrequency.MEDIUM,
    PageType.NEWS_INDEX: MonitoringFrequency.MEDIUM,
    PageType.ARTICLE: MonitoringFrequency.DISABLED,
    PageType.POLICY_PAGE: MonitoringFrequency.STANDARD,
    PageType.TEAM_PAGE: MonitoringFrequency.STANDARD,
    PageType.EVENTS: MonitoringFrequency.STANDARD,
    PageType.FUNDRAISING: MonitoringFrequency.STANDARD,
    PageType.STATIC: MonitoringFrequency.WEEKLY,
    PageType.IGNORE: MonitoringFrequency.DISABLED,
    PageType.UNKNOWN: MonitoringFrequency.LOW,
}

# Convert frequency to seconds
FREQUENCY_SECONDS = {
    MonitoringFrequency.REALTIME: 300,
    MonitoringFrequency.HIGH: 900,
    MonitoringFrequency.MEDIUM: 1800,
    MonitoringFrequency.STANDARD: 7200,
    MonitoringFrequency.LOW: 21600,
    MonitoringFrequency.WEEKLY: 604800,
    MonitoringFrequency.DISABLED: 0,
}


class DiffType(str, Enum):
    NEW_PAGE = "new_page"
    CONTENT_CHANGED = "content_changed"
    PAGE_REMOVED = "page_removed"
    STRUCTURAL_CHANGE = "structural_change"
    METADATA_CHANGE = "metadata_change"


class SignalSource(str, Enum):
    SCRAPLING = "scrapling"
    WORLDMONITOR = "worldmonitor"
    MIROFISH = "mirofish"
    MANUAL = "manual"


class SignalCategory(str, Enum):
    FINANCE = "finance"
    GEOPOLITICAL = "geopolitical"
    SUPPLY_CHAIN = "supply_chain"
    CYBER = "cyber"
    CLIMATE = "climate"
    POLITICS = "politics"
    HEALTHCARE = "healthcare"
    ECONOMY = "economy"
    CRIME = "crime"
    EDUCATION = "education"
    TECHNOLOGY = "technology"
    OTHER = "other"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    POLITICAL_PARTY = "political_party"
    MEDIA = "media"
    GOVERNMENT = "government"
    NGO = "ngo"
    BUSINESS = "business"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    BUILDING_GRAPH = "building_graph"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class AntiBotLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
