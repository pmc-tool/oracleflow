from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedArticle(BaseModel):
    title: str
    summary: str = ""
    url: str = ""
    source: str = ""
    published: Optional[datetime] = None
    country_code: str = ""
    category: str = "other"
