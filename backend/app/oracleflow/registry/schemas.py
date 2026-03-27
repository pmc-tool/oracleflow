"""Pydantic models for country source registry configuration."""

from pydantic import BaseModel, Field

from app.oracleflow.constants import AntiBotLevel


class NewsSource(BaseModel):
    """A news website to monitor."""

    url: str
    frequency: str = "15m"
    anti_bot: str = AntiBotLevel.LOW.value
    selectors: dict = Field(default_factory=dict)


class RedditSource(BaseModel):
    """A Reddit subreddit to monitor."""

    subreddit: str
    frequency: str = "15m"


class GovernmentSource(BaseModel):
    """A government website to monitor."""

    url: str
    type: str
    frequency: str = "2h"


class SocialSource(BaseModel):
    """Social media accounts to monitor."""

    facebook_pages: list[str] = Field(default_factory=list)
    twitter_accounts: list[str] = Field(default_factory=list)


class PoliticalEntity(BaseModel):
    """A political party or entity to track."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    website: str = ""
    leader: str = ""


class CountrySources(BaseModel):
    """All source types for a country."""

    news: list[NewsSource] = Field(default_factory=list)
    reddit: list[RedditSource] = Field(default_factory=list)
    government: list[GovernmentSource] = Field(default_factory=list)
    social: SocialSource = Field(default_factory=SocialSource)
    political_entities: list[PoliticalEntity] = Field(default_factory=list)


class CountryConfig(BaseModel):
    """Full configuration for a monitored country."""

    country: str
    code: str
    region: str
    languages: list[str]
    timezone: str
    proxy_pool: str = ""
    sources: CountrySources
