import asyncio
import logging
from pathlib import Path

from src.adapters.meta import MetaAdapter

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUT_DIR = Path("data")


async def main():
    adapter = MetaAdapter(output_dir=OUTPUT_DIR)

    # 1. 获取文章 URL 列表
    logging.info("Fetching article URLs...")
    url_list = await adapter.fetch()
    logging.info(f"Found {len(url_list)} articles")

    if not url_list:
        logging.warning("No articles found")
        return

    # 2. 解析文章内容
    logging.info("Parsing articles...")
    articles = await adapter.parse(url_list)
    logging.info(f"Parsed {len(articles)} articles")

    if not articles:
        logging.warning("No articles parsed")
        return

    # 3. 保存文章
    logging.info("Saving articles...")
    await adapter.save(articles)
    logging.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
