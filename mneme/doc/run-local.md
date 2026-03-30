# Run Mneme Locally

## Prerequisites

- Python 3.13+
- `uv` installed and available in `PATH`

## Quick Start

From the repository root:

```bash
bash mneme/scripts/start_dev.sh
```

The script will:

1. enter `mneme/`
2. load `.env` automatically if it exists
3. read `config.yaml` automatically if it exists
4. run `uv sync --extra dev`
5. start the FastAPI app at `http://127.0.0.1:8000`

If `mneme/src/frontend/dist` already exists, FastAPI will also serve the built Vue frontend on `/`.

## Frontend Development

Use two processes during frontend development:

Terminal 1:

```bash
bash mneme/scripts/start_dev.sh
```

Terminal 2:

```bash
bash mneme/scripts/start_frontend_dev.sh
```

Then open `http://127.0.0.1:5173`.

The Vite dev server proxies `/api/*` to the FastAPI backend at `http://127.0.0.1:8000`, so the Vue app can call the same relative API paths in development and production.

## Build Frontend For Backend Serving

To let FastAPI serve the Vue app directly from `mneme/src/frontend/dist`:

```bash
bash mneme/scripts/build_frontend.sh
```

After the build finishes, open `http://127.0.0.1:8000`.

## Recommended Config: YAML

Copy the example file first:

```bash
cd mneme
cp config.yaml.example config.yaml
```

Then edit `mneme/config.yaml`:

```yaml
app:
  name: Mneme
  database_path: data/mneme.db
  max_articles_per_source: 3

anthropic:
  base_url: null
  model: claude-sonnet-4-20250514
  api_key: your_anthropic_key

scheduler:
  enabled: true
  hour: 9
  minute: 0
  timezone: Asia/Shanghai

notifications:
  telegram:
    bot_token: your_bot_token
    chat_id: your_chat_id
  feishu:
    app_id: your_app_id
    app_secret: your_app_secret
    user_id: your_open_id
```

If `anthropic.api_key` is not set, Mneme still runs, but uses fallback local summaries instead of the Anthropic API.

If you use MiniMax's Anthropic-compatible endpoint, set:

```yaml
anthropic:
  base_url: https://api.minimaxi.com/anthropic
  model: MiniMax-M2.7
  api_key: your_minimax_key
```

MiniMax documents this compatibility mode as requiring `ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic` while still using the Anthropic SDK.

## Optional Overrides: Environment Variables

Environment variables still work and take precedence over `config.yaml`.

Useful examples:

```bash
ANTHROPIC_API_KEY=your_anthropic_key
MNEME_SCHEDULER_ENABLED=true
MNEME_SCHEDULER_HOUR=10
MNEME_CONFIG_PATH=config.yaml
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_USER_ID=your_open_id
```

## Use the App

- Open `http://127.0.0.1:5173` for Vite development, or `http://127.0.0.1:8000` after building the frontend
- Click `Run now` to trigger a manual sync
- Click `Reset` to clear collected articles before re-fetching them
- Use the scheduler form to enable or change the daily run time
- Read collected summaries from the article list

## Useful Commands

```bash
cd mneme
uv run pytest
uv run ruff check .
uv run mypy main.py src
bash scripts/build_frontend.sh
```

## Historical Backfill

To backfill the longform engineering sources up to a cutoff date without sending IM notifications:

```bash
bash mneme/scripts/backfill.sh 2026-03-29
```

To backfill only selected sources:

```bash
bash mneme/scripts/backfill.sh 2026-03-29 openai_engineering,anthropic_engineering,meta_engineering,google_cloud_devops_sre
```

Current backfill scope is the 4 longform sources:

- `openai_engineering`
- `anthropic_engineering`
- `meta_engineering`
- `google_cloud_devops_sre`

The newsletter sources and the SREcon schedule should still be handled as separate source types in a later phase.
