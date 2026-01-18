from datetime import datetime
from pydantic import BaseModel


class Article(BaseModel):
    id: str
    source: str
    title: str
    published_at: datetime
    url: str
    raw_content: str = ""
    raw_context_path: str = ""
