from abc import ABC, abstractmethod
from pathlib import Path
from ..models.article import Article

class BaseAdapter(ABC):
    def __init__(self, output_dir: Path | str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def fetch(self) ->list[str]:
        pass

    @abstractmethod
    async def parse(self,url_list: list[str]) ->list[Article]:
        pass

    @abstractmethod
    async def save(self, articles: list[Article]) -> list[Path]:
        pass

    async def run(self) -> list[Article]:
        urls = await self.fetch()
        articles = self.parse(urls)
        await self.save(articles)
        return articles
