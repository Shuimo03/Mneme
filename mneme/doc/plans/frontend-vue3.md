# Frontend Vue3 Implementation Plan

## Overview

Rewrite the existing vanilla JavaScript frontend using Vue 3 with Composition API, HeroUI component library, and Tailwind CSS.

## Requirements

- Framework: Vue 3 with Composition API
- UI Library: HeroUI (https://heroui.com/)
- CSS Framework: Tailwind CSS (https://tailwindcss.com/)
- No emojis in code

## Current Implementation

Existing files in `src/frontend/`:
- `index.html` - Vue app entry point
- `package.json` - Dependencies
- `vite.config.js` - Vite configuration
- `tailwind.config.js` - Tailwind configuration
- `src/` - Vue components and composables

## Target Features (Preserved)

1. **Status Display**: Shows scheduler state, last run info, Anthropic status, delivery channels
2. **Articles List**: Displays collected articles with source, title, summary, bullets, tags
3. **Manual Run**: Button to trigger immediate sync
4. **Scheduler Configuration**: Enable/disable + set hour/minute
5. **Refresh**: Reload data from API

## Project Structure

```
src/frontend/
  index.html              # HTML entry point
  package.json            # Dependencies
  vite.config.js          # Vite configuration
  tailwind.config.js      # Tailwind configuration
  postcss.config.js       # PostCSS configuration
  src/
    main.js               # Vue app bootstrap
    App.vue               # Root component
    style.css             # Tailwind imports + custom styles
    components/
      StatusCard.vue      # Status display card
      StatusGrid.vue      # Grid of status cards
      ArticleCard.vue     # Individual article display
      ArticleList.vue     # List of articles
      SchedulerForm.vue   # Scheduler configuration form
      ActionButtons.vue   # Run now and refresh buttons
    composables/
      useApi.js           # API fetching composable
```

## Component Design

### App.vue
Root component managing:
- Fetching status and articles data
- Handling manual run, refresh, scheduler update
- Layout with hero section, status grid, article list

### StatusCard.vue
Props: `label`, `title`, `description`
Displays a status metric in a card format.

### StatusGrid.vue
Renders 4 status cards:
- Schedule (enabled/disabled, time, timezone)
- Last run (status, message)
- Anthropic (configured/fallback)
- Delivery (Telegram/Feishu status)

### ArticleCard.vue
Props: `article` object
Displays:
- Source badge
- Title (link to original)
- Summary text
- Bullet points list
- Tags row

### SchedulerForm.vue
Props: `scheduler` object
Events: `@update`
Controls:
- Enable/disable checkbox
- Hour input
- Minute input

### ActionButtons.vue
Props: `loading`
Events: `@run`, `@refresh`
Buttons:
- "Run now" primary button
- "Refresh" secondary button

## API Integration

Endpoints (preserved from existing):
- `GET /api/status` - Fetch system status
- `GET /api/articles` - Fetch articles list
- `POST /api/runs/sync` - Trigger manual sync
- `POST /api/scheduler` - Update scheduler config
- Backend responses should be declared with explicit FastAPI `response_model` types
- Frontend API consumers should use TypeScript interfaces that mirror the backend payloads

Development mode:
- Run the FastAPI backend on `http://127.0.0.1:8000`
- Run the Vite dev server on `http://127.0.0.1:5173`
- Use the Vite proxy so Vue calls relative `/api/*` URLs without CORS-specific code

Integrated serving mode:
- Build the frontend into `src/frontend/dist`
- Let FastAPI serve `dist/index.html` at `/`
- Let FastAPI serve `dist/assets/*` directly
- Use SPA fallback routing for non-API frontend paths

## Build Process

The Vue project will be built using Vite. The `dist/` output is the final static bundle served by the Python backend.

## Implementation Steps

1. Create package.json with Vue 3, Vite, Tailwind, HeroUI dependencies
2. Create Vite, Tailwind, PostCSS configurations
3. Create index.html entry point
4. Create main.js Vue bootstrap
5. Create App.vue root component
6. Create composables/useApi.js for API calls
7. Create StatusCard.vue
8. Create StatusGrid.vue
9. Create ArticleCard.vue
10. Create ArticleList.vue
11. Create SchedulerForm.vue
12. Create ActionButtons.vue
13. Create style.css with Tailwind imports
14. Remove old app.js and styles.css

## Color Scheme (Preserved)

Maintain the existing warm cream aesthetic:
- Background: `#f4ecdf` / `#fbf5ea`
- Panel: `rgba(255, 249, 240, 0.92)` / `#fffdf8`
- Text: `#1f2a33`
- Muted: `#6d7468`
- Accent: `#0d7c6c` / `#0b5f54`
- Accent soft: `#d7f1ea`
- Accent warm: `#f1c97f`
- Border: `rgba(96, 82, 62, 0.18)`

These will be configured in Tailwind theme extension.
