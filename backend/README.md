# token-usage-backend

FastAPI + SQLite backend for Waka-Token. It receives `ccusage daily --instances --json` uploads, stores one row per `user_id + date + project + source`, serves public aggregation APIs, and generates real-time SVG badges for GitHub READMEs.

## Stack

- Python 3.11+
- FastAPI
- SQLite with WAL mode and busy timeout
- SQLAlchemy
- Alembic
- Docker

## Local Run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The app also creates tables on startup for quick MVP runs. Alembic is included for deployable schema history.

## Docker Run

```powershell
cd backend
docker compose up --build
```

API URL:

```text
http://127.0.0.1:8000
```

## Upload ccusage Data

Clients can run this about every 5 minutes:

```powershell
ccusage daily --instances --json | Out-File -Encoding utf8 ccusage.json
$body = @{
  user_id = "jun"
  source = "claude-code"
  hostname = $env:COMPUTERNAME
  ccusage = Get-Content .\ccusage.json -Raw | ConvertFrom-Json
} | ConvertTo-Json -Depth 20
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/collect -Body $body -ContentType "application/json"
```

Linux cron-style loop:

```bash
while true; do
  ccusage daily --instances --json > /tmp/ccusage.json
  jq -n --arg user_id "$USER" --arg source "ccusage" --slurpfile ccusage /tmp/ccusage.json \
    '{user_id: $user_id, source: $source, ccusage: $ccusage[0]}' |
    curl -sS -X POST http://127.0.0.1:8000/api/collect \
      -H 'Content-Type: application/json' \
      --data-binary @-
  sleep 300
done
```

Supported upload aliases:

- `POST /api/collect`
- `POST /api/reports`
- `POST /api/usage/upload`

No authentication is required for the MVP.

## API

### Collection

```http
POST /api/collect
```

Body:

```json
{
  "user_id": "jun",
  "source": "claude-code",
  "hostname": "devbox",
  "ccusage": {
    "projects": {
      "token-usage-backend": [
        {
          "date": "2026-05-30",
          "inputTokens": 277,
          "outputTokens": 31456,
          "cacheCreationTokens": 512,
          "cacheReadTokens": 1024,
          "totalTokens": 33269,
          "totalCost": 17.58,
          "modelsUsed": ["gpt-5-codex"]
        }
      ]
    }
  }
}
```

Upsert key:

```text
user_id + date + project + source
```

`source` is a free-form string, so all ccusage-supported CLIs can be represented without schema changes.

### Public Query APIs

```http
GET /api/users
GET /api/summary?userId=jun
GET /api/usage/daily?userId=jun&from=2026-05-01&to=2026-05-30
GET /api/usage/projects?userId=jun
GET /api/usage/sources?userId=jun
GET /api/usage/models?userId=jun
GET /api/usage/aggregate?group_by=project&userId=jun
```

Both `user_id` and `userId` query parameters are accepted.

### SVG Badge APIs

```http
GET /api/badge.svg?userId=jun&type=monthly&style=flat&color=auto
GET /badge/jun.svg?type=total&style=flat-square&color=green
```

Supported badge types:

- `daily`
- `monthly`
- `total`
- `cost`

Supported styles:

- `flat`
- `flat-square`
- `for-the-badge`

GitHub README example:

```md
![Token Usage](https://your-domain.example/api/badge.svg?userId=jun&type=monthly&style=flat&color=auto)
```

## Static SVG Badge Generation

Generate SVG files from a running API:

```powershell
python scripts/generate_static_badges.py --base-url http://127.0.0.1:8000 --user-id jun --output-dir badges
```

This creates:

```text
badges/jun-daily.svg
badges/jun-monthly.svg
badges/jun-total.svg
badges/jun-cost.svg
```

## Tests

```powershell
pip install -e ".[dev]"
pytest
```

## Notes

- MVP has no authentication.
- Query APIs and SVG badge APIs are public.
- SQLite uses WAL mode and a 5-second busy timeout.
- The backend accepts standard `daily`, `data`, and `projects`-grouped ccusage JSON shapes.
- ccusage JSON reference: https://ccusage.com/guide/json-output
