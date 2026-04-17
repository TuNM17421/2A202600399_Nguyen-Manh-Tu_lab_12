# Deployment Information

## Student
- Name: Nguyễn Mạnh Tú
- Student ID: 2A202600399
- Date: 2026-04-17

## Public URL
https://2a202600399nguyen-manh-tulab12-production.up.railway.app/

## Platform
Railway

## Verified Status
- `GET /health` was checked successfully and returned HTTP `200`.
- `POST /ask` without `X-API-Key` was checked successfully and returned HTTP `401`.

## Test Commands

### Health Check
```bash
curl https://2a202600399nguyen-manh-tulab12-production.up.railway.app/health
```

Expected sample response:
```json
{"status":"ok","version":"1.0.0","environment":"production"}
```

### Authentication Required
```bash
curl -X POST https://2a202600399nguyen-manh-tulab12-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

Expected: `401 Unauthorized`

### API Test (with authentication)
```bash
curl -X POST https://2a202600399nguyen-manh-tulab12-production.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

Expected: `200 OK` with JSON answer payload.

## Environment Variables Set
- `PORT`
- `ENVIRONMENT`
- `OPENAI_API_KEY`
- `AGENT_API_KEY`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `REDIS_URL`
- `ALLOWED_ORIGINS`

## Screenshots
Add your screenshots into the `screenshots/` folder:
- `screenshots/dashboard.png`
- `screenshots/running.png`
- `screenshots/test-results.png`

## Notes
This deployment is based on the production-ready app in `06-lab-complete/` and is configured for Railway hosting.
