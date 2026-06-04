---
name: service-orchestrator
description: Service lifecycle management for backend Python API, Node I/O, Rust indexer, and frontend Vite services. Load this skill when you need to bring up the target application or manage running services during testing.
allowed-tools:
  - shell
  - http
  - file_read
  - web_fetch
---

# Service orchestrator lifecycle playbook

Use this skill to start, verify, and stop the Aegix local services.

| Service | Location | Port |
|---|---|---|
| Backend Python API | `backend/` | 8000 |
| Backend Node I/O | `backend/node/` | 7001 |
| Backend Rust indexer | `backend/rust-indexer/` | 7100 |
| Frontend Vite dev server | repository root | 8080 |

## 1. Prerequisites check

Before starting anything:

- Verify Python 3.14+ is available: `python --version`
- Verify Bun is available: `bun --version`
- Verify pnpm is available for Node I/O: `pnpm --version`
- Verify Cargo is available if Rust auto-build is enabled: `cargo --version`
- Check backend `.env` exists and has the required provider keys
- Check no stale processes on target ports:
  - `Get-NetTCPConnection -LocalPort 8000,7001,7100,8080 -ErrorAction SilentlyContinue` on Windows
  - `lsof -ti:8000,7001,7100,8080 2>/dev/null` on Linux/macOS

## 2. Start backend

```powershell
# From the repository root
cd backend
python main.py
```

This starts the FastAPI Python API on 8000, Node I/O on 7001, and the Rust indexer on 7100 when its binary is built. The process runs in the foreground, so run it in a separate terminal or background process.

To run in background on Windows:

```powershell
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "backend" -RedirectStandardOutput "backend.log" -RedirectStandardError "backend-err.log"
```

Wait 5 seconds, then verify:

```powershell
Start-Sleep -Seconds 5
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health/live
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7001/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7100/health
```

Python and Node should return `200`. Rust returns `200` only when `backend/rust-indexer` has been built.

## 3. Start frontend

```powershell
# From the repository root, in a separate terminal
bun run dev
```

To run in background on Windows:

```powershell
Start-Process -NoNewWindow -FilePath "bun" -ArgumentList "run dev" -WorkingDirectory "." -RedirectStandardOutput "frontend.log" -RedirectStandardError "frontend-err.log"
```

Verify:

```powershell
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080
```

Expected: `200`.

## 4. Health check

```powershell
curl -s http://127.0.0.1:8000/api/v1/health/live
curl -s http://127.0.0.1:7001/health
curl -s http://127.0.0.1:7100/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080
```

## 5. Stop services

```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Id (Get-NetTCPConnection -LocalPort 7001 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Id (Get-NetTCPConnection -LocalPort 7100 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Id (Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
```

On Linux/macOS:

```bash
kill $(lsof -ti:8000) 2>/dev/null; kill $(lsof -ti:7001) 2>/dev/null; kill $(lsof -ti:7100) 2>/dev/null; kill $(lsof -ti:8080) 2>/dev/null; true
```

Always verify with an actual HTTP request. A live process does not guarantee service readiness.
