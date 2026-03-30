"""FastAPI application for Mneme."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from .collector import CollectorService
from .database import Database
from .logging_config import configure_logging
from .models.api import (
    ResetArticlesResponse,
    RunResponse,
    SchedulerResponse,
    StatusCapabilities,
    StatusResponse,
)
from .models.article import Article, SchedulerState, SchedulerUpdate
from .network import disable_proxy_env
from .notifier import NotifierService
from .settings import load_settings
from .source_registry import build_longform_sources
from .summarizer import SummarizerService


def _frontend_paths() -> tuple[Path, Path, Path]:
    base_dir = Path(__file__).resolve().parent
    frontend_root = base_dir / "frontend"
    frontend_dist = frontend_root / "dist"
    frontend_index = frontend_dist / "index.html"
    return frontend_root, frontend_dist, frontend_index


def _resolve_frontend_file(frontend_dist: Path, requested_path: str) -> Path | None:
    if not requested_path:
        return None

    frontend_root = frontend_dist.resolve()
    candidate = (frontend_dist / requested_path.lstrip("/")).resolve()
    if not candidate.is_relative_to(frontend_root):
        return None
    if not candidate.is_file():
        return None
    return candidate


def _frontend_placeholder(app_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{app_name}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f4ecdf;
        --panel: rgba(255, 249, 240, 0.95);
        --border: rgba(96, 82, 62, 0.18);
        --text: #1f2a33;
        --muted: #6d7468;
        --accent: #0d7c6c;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at top left, rgba(241, 201, 127, 0.35), transparent 35%),
          linear-gradient(180deg, #fbf5ea 0%, var(--bg) 100%);
        color: var(--text);
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        padding: 24px;
      }}

      main {{
        width: min(720px, 100%);
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 32px;
        box-shadow: 0 24px 80px rgba(28, 33, 33, 0.08);
      }}

      h1 {{
        margin: 0 0 12px;
        font-size: clamp(2rem, 4vw, 3rem);
      }}

      p {{
        margin: 0 0 14px;
        line-height: 1.6;
      }}

      code {{
        background: rgba(13, 124, 108, 0.08);
        border-radius: 8px;
        padding: 0.15rem 0.4rem;
        font-family: "SFMono-Regular", "SF Mono", Consolas, monospace;
      }}

      .hint {{
        color: var(--muted);
      }}

      .accent {{
        color: var(--accent);
        font-weight: 600;
      }}
    </style>
  </head>
  <body>
    <main>
      <p class="accent">Frontend build not found</p>
      <h1>{app_name}</h1>
      <p>The FastAPI backend is running, but the Vue frontend has not been built yet.</p>
      <p>For local frontend development, run <code>bash mneme/scripts/start_frontend_dev.sh</code> and open <code>http://127.0.0.1:5173</code>.</p>
      <p>To let FastAPI serve the frontend directly, run <code>bash mneme/scripts/build_frontend.sh</code> and refresh this page.</p>
      <p class="hint">API endpoints remain available under <code>/api/*</code>.</p>
    </main>
  </body>
</html>
"""


def create_app() -> FastAPI:
    disable_proxy_env()
    settings = load_settings()
    configure_logging()
    database = Database(settings.database_path)
    database.initialize()

    scheduler_state = database.ensure_scheduler_state(
        SchedulerState(
            enabled=settings.scheduler_enabled,
            hour=settings.scheduler_hour,
            minute=settings.scheduler_minute,
            timezone=settings.scheduler_timezone,
        )
    )

    collector = CollectorService(
        repository=database,
        summarizer=SummarizerService(settings),
        notifier=NotifierService(settings),
        sources=build_longform_sources(),
        max_articles_per_source=settings.max_articles_per_source,
    )
    scheduler = AsyncIOScheduler(timezone=scheduler_state.timezone)
    _, frontend_dist, frontend_index = _frontend_paths()

    def reschedule_job() -> SchedulerState:
        state = database.get_scheduler_state()
        scheduler.remove_all_jobs()
        if state.enabled:
            scheduler.add_job(
                collector.run_once,
                CronTrigger(hour=state.hour, minute=state.minute, timezone=state.timezone),
                args=["scheduled"],
                id="digest-job",
                replace_existing=True,
            )
        return state

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        scheduler.start()
        reschedule_job()
        yield
        scheduler.shutdown(wait=False)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    frontend_assets = frontend_dist / "assets"
    if frontend_assets.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_assets)),
            name="frontend-assets",
        )
    app.state.settings = settings
    app.state.database = database
    app.state.collector = collector
    app.state.scheduler = scheduler
    app.state.reschedule_job = reschedule_job

    @app.get("/", include_in_schema=False)
    async def index() -> Response:
        if frontend_index.is_file():
            return FileResponse(frontend_index)
        return HTMLResponse(_frontend_placeholder(settings.app_name))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/articles", response_model=list[Article])
    async def list_articles(limit: int = 50) -> list[Article]:
        return database.list_articles(limit=limit)

    @app.delete("/api/articles", response_model=ResetArticlesResponse)
    async def reset_articles() -> ResetArticlesResponse:
        deleted = database.clear_articles()
        return ResetArticlesResponse(deleted=deleted)

    @app.get("/api/status", response_model=StatusResponse)
    async def get_status() -> StatusResponse:
        current_state = database.get_scheduler_state()
        last_run = database.get_last_run()
        return StatusResponse(
            scheduler=current_state,
            last_run=last_run,
            capabilities=StatusCapabilities(
                anthropic_configured=bool(settings.anthropic_api_key),
                telegram_enabled=settings.telegram_enabled,
                feishu_enabled=settings.feishu_enabled,
            ),
        )

    @app.post("/api/scheduler", response_model=SchedulerResponse)
    async def update_scheduler(payload: SchedulerUpdate) -> SchedulerResponse:
        database.update_scheduler_state(
            SchedulerState(
                enabled=payload.enabled,
                hour=payload.hour,
                minute=payload.minute,
                timezone=settings.scheduler_timezone,
            )
        )
        updated_state = reschedule_job()
        return SchedulerResponse(scheduler=updated_state)

    @app.post("/api/runs/sync", response_model=RunResponse)
    async def run_sync() -> RunResponse:
        run = await collector.run_once(trigger="manual")
        return RunResponse(run=run)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend_routes(full_path: str) -> Response:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)

        if frontend_index.is_file():
            frontend_file = _resolve_frontend_file(frontend_dist, full_path)
            if frontend_file is not None:
                return FileResponse(frontend_file)
            if "." in Path(full_path).name:
                raise HTTPException(status_code=404)
            return FileResponse(frontend_index)

        if "." in full_path:
            raise HTTPException(status_code=404)
        return HTMLResponse(_frontend_placeholder(settings.app_name))

    return app
