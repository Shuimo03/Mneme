"""Historical backfill command for Mneme longform sources."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from .database import Database
from .logging_config import bind_logger, configure_logging, get_logger
from .models.article import RunRecord, SourceState
from .network import disable_proxy_env
from .notifier import NotifierService
from .settings import load_settings
from .source_registry import build_longform_sources
from .summarizer import SummarizerService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill historical Mneme sources.")
    parser.add_argument(
        "--until",
        default="2026-03-29",
        help="Inclusive cutoff date in YYYY-MM-DD.",
    )
    parser.add_argument(
        "--sources",
        default="",
        help="Comma-separated source names. Defaults to all longform sources.",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send notifications after the backfill finishes.",
    )
    return parser.parse_args()


async def run_backfill(until: datetime, selected_sources: set[str], notify: bool) -> int:
    disable_proxy_env()
    settings = load_settings()
    configure_logging()
    logger = bind_logger(get_logger(__name__), source="backfill", stage="run", run_id="backfill")
    database = Database(settings.database_path)
    database.initialize()

    summarizer = SummarizerService(settings)
    notifier = NotifierService(settings)
    sources = [
        source
        for source in build_longform_sources()
        if not selected_sources or source.name in selected_sources
    ]

    all_new_articles = []
    for source in sources:
        logger.info("Backfilling source=%s until=%s", source.name, until.date())
        database.update_source_state(
            SourceState(
                source=source.name,
                cursor=until.date().isoformat(),
                status="running",
                message="Backfill in progress.",
            )
        )

        try:
            seeds = await source.fetch_history(until=until)
            processed = []
            for seed in seeds:
                if database.article_exists(seed.url):
                    continue
                article = await source.fetch_article(seed)
                article = await summarizer.summarize(article)
                database.save_article(article)
                processed.append(article)

            if notify and processed:
                sent_channels = await notifier.send_digest(processed)
                if sent_channels > 0:
                    database.mark_articles_notified([article.url for article in processed])

            database.update_source_state(
                SourceState(
                    source=source.name,
                    cursor=until.date().isoformat(),
                    status="completed",
                    message=f"Backfilled {len(processed)} new articles.",
                )
            )
            all_new_articles.extend(processed)
        except Exception as exc:
            database.update_source_state(
                SourceState(
                    source=source.name,
                    cursor=until.date().isoformat(),
                    status="failed",
                    message=str(exc),
                )
            )
            raise

    database.record_run(
        RunRecord.succeeded(
            trigger="backfill",
            processed_count=len(all_new_articles),
            notified_channels=0,
            message=f"Historical backfill completed up to {until.date().isoformat()}",
        )
    )
    logger.info(
        "Backfill completed sources=%s new_articles=%s",
        len(sources),
        len(all_new_articles),
    )
    return len(all_new_articles)


def main() -> None:
    args = parse_args()
    until = datetime.strptime(args.until, "%Y-%m-%d").replace(tzinfo=UTC)
    selected_sources = {
        source.strip()
        for source in args.sources.split(",")
        if source.strip()
    }
    count = asyncio.run(
        run_backfill(
            until=until,
            selected_sources=selected_sources,
            notify=args.notify,
        )
    )
    print(f"Backfill completed. New articles saved: {count}")


if __name__ == "__main__":
    main()
