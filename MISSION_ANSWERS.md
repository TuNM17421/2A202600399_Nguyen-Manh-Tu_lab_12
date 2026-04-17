# Day 12 Lab - Mission Answers

**Student Name:** Nguyễn Mạnh Tú  
**Student ID:** 2A202600399  
**Date:** 2026-04-17

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secrets in source code are unsafe and can leak when pushed to GitHub.
2. Hardcoded host/port values make the app difficult to deploy on cloud platforms.
3. Missing health checks prevents Railway, Render, or Docker from detecting app failures.
4. Using plain `print()` for logs is not suitable for production monitoring.
5. No graceful shutdown can interrupt in-flight requests during deploy or restart.
6. Missing authentication exposes the API publicly.
7. No rate limiting allows abuse and unexpected cost spikes.
8. Business logic stored only in memory makes scaling unreliable.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded / simple | Environment-based config | Safe and portable |
| Secrets | Often inline | Loaded from env vars | Prevent secret leaks |
| Logging | `print()` | Structured JSON logs | Easier monitoring |
| Health checks | Usually absent | `/health` and `/ready` | Platform can restart failed app |
| Auth | None or basic | API key protection | Blocks unauthorized usage |
| Rate limiting | Not enforced | 10 req/min | Protects service availability |
| Cost guard | Not tracked | Budget limit enabled | Prevents overspending |
| Scaling | Single process | Stateless-ready design | Supports multi-instance deployment |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11-slim`
2. **Working directory:** `/app`
3. **Why copy requirements first?** To take advantage of Docker layer caching and speed up rebuilds.
4. **Why use a non-root user?** It improves container security.
5. **Why multi-stage build?** It reduces the final image size and removes unnecessary build tools.

### Exercise 2.3: Image size comparison
- Develop: larger image because it includes more tools and less optimization
- Production: smaller image due to `slim` base and multi-stage build
- Difference: production image is significantly smaller and safer for deployment

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **Platform:** Railway
- **Public URL:** https://2a202600399nguyen-manh-tulab12-production.up.railway.app/
- **Status:** Deployed successfully and health endpoint is reachable
- **Why Railway?** Fast setup, simple deployment flow, and easy environment variable management

### Deployment notes
1. Push code to GitHub.
2. Connect the repository to Railway.
3. Set required environment variables.
4. Deploy the app and verify `/health`.

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- `GET /health` returns HTTP `200` and status `ok`.
- `POST /ask` without API key returns HTTP `401`.
- `POST /ask` with a valid API key is designed to return HTTP `200` and a JSON answer.
- Rate limiting is configured to restrict usage per user.

### Exercise 4.4: Cost guard implementation
I implemented a configurable budget guard to estimate token cost for each request and stop usage when the configured limit is exceeded. This helps prevent unexpected API spending in production.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- Added structured logging for better observability.
- Implemented health and readiness endpoints.
- Added graceful shutdown handling for safer restarts.
- Prepared Redis-backed rate limiting and budget tracking with fallback support.
- Kept the service production-oriented for cloud deployment.

### Final reflection
This lab showed the difference between an app that works on localhost and one that is ready for real production deployment. The final version is more secure, easier to monitor, and safer to operate in the cloud.
