---
created: 2026-05-02
updated: 2026-05-02
tags:
  - django
  - dev-ops
  - localtunnel
  - tmux
  - documentation
type: resource
status: active
---

# Unified Local Development & Subdomain Setup

This document describes how to implement a unified development script (`dev.sh`) that uses `tmux` and `localtunnel` to provide a seamless, port-free local development environment with subdomains.

## 🚀 Overview

The goal is to start all project services (Django, Celery, Frontend, Tunnels) with a single command and access the application via a persistent, secure URL like `https://project-name.loca.lt`.

## 📦 Prerequisites

Ensure the following are installed on the development machine:
- **`tmux`**: Terminal multiplexer for managing background processes.
- **`localtunnel`**: Exposes local ports to the internet (`npm install -g localtunnel`).
- **`python-decouple`**: For managing environment-based settings in Django.

---

## 🛠️ Step 1: Django Configuration

To allow traffic from the localtunnel subdomain, update `settings.py`.

### `project/settings.py`

```python
from decouple import config, Csv

# ALLOWED_HOSTS must include the localtunnel domain
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", 
    default="localhost,127.0.0.1,project-name.loca.lt", 
    cast=Csv()
)

# CSRF_TRUSTED_ORIGINS is required for secure requests via the tunnel
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS", 
    default="https://project-name.loca.lt,http://project-name.loca.lt", 
    cast=Csv()
)
```

---

## ⚙️ Step 2: Environment Variables

Update `.env.example` to provide the correct defaults for team members.

```env
ALLOWED_HOSTS=localhost,127.0.0.1,project-name.loca.lt
CSRF_TRUSTED_ORIGINS=https://project-name.loca.lt
```

---

## 📜 Step 3: The Unified `dev.sh` Script

Create a `dev.sh` file in the project root. This script handles virtual environment detection, port conflict resolution, and service orchestration.

### Basic Template (Port Detection + Unset Logic)

```bash
#!/bin/bash

# 1. Project Identity
PROJECT_NAME=$(basename "$PWD")
SESSION_NAME="${PROJECT_NAME}_dev"
SUBDOMAIN="${PROJECT_NAME}"

# 2. Check for existing session
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

# 3. Prevent Environment Overrides
# Forces Django to read from .env instead of inherited shell exports
unset ALLOWED_HOSTS
unset CSRF_TRUSTED_ORIGINS

# 4. Dynamic Port Detection (starts at 8000)
PORT=8000
while ss -tuln | grep -q ":$PORT " ; do
    PORT=$((PORT+1))
done

# 5. Virtual Env Detection
VENV_CMD=""
[ -d "venv" ] && VENV_CMD="source venv/bin/activate && "
[ -d ".venv" ] && VENV_CMD="source .venv/bin/activate && "
```

---

## 🏗️ Case Studies

### Case A: Vanilla Django Project
Focuses strictly on the Django server and the tunnel.

```bash
# Add to dev.sh
tmux new-session -d -s $SESSION_NAME -n 'django' -c "$PWD" "${VENV_CMD}python manage.py runserver $PORT"
tmux new-window -n 'tunnel' -c "$PWD" "npx localtunnel --port $PORT --subdomain $SUBDOMAIN"
tmux select-window -t $SESSION_NAME:0
tmux attach -t $SESSION_NAME
```

### Case B: Complex Django (Celery + Redis + Stripe)
Ideal for projects with background tasks and external webhooks.

```bash
# Add to dev.sh
tmux new-session -d -s $SESSION_NAME -n 'django' -c "$PWD" "${VENV_CMD}python manage.py runserver $PORT"
tmux new-window -n 'worker' -c "$PWD" "${VENV_CMD}celery -A config worker -l info"
tmux new-window -n 'beat' -c "$PWD" "${VENV_CMD}celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
tmux new-window -n 'stripe' -c "$PWD" "stripe listen --forward-to localhost:$PORT/payments/webhook/"
tmux new-window -n 'tunnel' -c "$PWD" "npx localtunnel --port $PORT --subdomain $SUBDOMAIN"
```

### Case C: Monorepo (Frontend + Backend)
For projects with separate frontend (React/Astro/Next.js) and Django backend.

```bash
# Add to dev.sh
# Assume backend is in ./backend and frontend in ./frontend
tmux new-session -d -s $SESSION_NAME -n 'backend' -c "$PWD/backend" "${VENV_CMD}python manage.py runserver $PORT"
tmux new-window -n 'frontend' -c "$PWD/frontend" "npm run dev"
tmux new-window -n 'tunnel' -c "$PWD" "npx localtunnel --port $PORT --subdomain $SUBDOMAIN"
```

---

## 💡 Important Considerations

### Port Conflict Resolution
The `ss -tuln` loop ensures that if you are working on multiple Django projects at once, they won't fight for port 8000. Each will automatically pick the next free port (8001, 8002, etc.), while `localtunnel` ensures the public URL remains consistent.

### Single Domain Access
By using the subdomain, you avoid "Port Hunting" in your browser. Always access the app via `https://project-name.loca.lt`. This is critical for:
1. **OAuth2**: Google/Microsoft only allow redirects to authorized domains.
2. **Webhooks**: Services like Stripe need a public URL to send events.
3. **Cookies/Sessions**: Prevents cross-project session interference on `localhost`.

### Tmux Usage
- `Ctrl+b` then `n`: Next window.
- `Ctrl+b` then `p`: Previous window.
- `Ctrl+b` then `d`: Detach (keep processes running in background).
- `./dev.sh`: Re-attach to the session.
