#!/bin/bash

SESSION_NAME="fastjob_dev"

# Check if session exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

echo "Creating new dev session: $SESSION_NAME"

# Unset environment variables that might override .env file
unset ALLOWED_HOSTS
unset CSRF_TRUSTED_ORIGINS

# Find a free port starting from 8000
PORT=8000
while ss -tuln | grep -q ":$PORT " ; do
    PORT=$((PORT+1))
done
echo "Using available port: $PORT"

# Detect virtual environment
VENV_CMD=""
if [ -d "venv" ]; then
    VENV_CMD="source venv/bin/activate && "
elif [ -d ".venv" ]; then
    VENV_CMD="source .venv/bin/activate && "
fi

# Create the session and the first window for Django dev server
tmux new-session -d -s $SESSION_NAME -n 'django' -c "$PWD" "${VENV_CMD}python manage.py runserver $PORT"

# Create a window for Celery Worker
tmux new-window -n 'celery-worker' -c "$PWD" "${VENV_CMD}celery -A config worker -l info -c 4"

# Create a window for Celery Beat
tmux new-window -n 'celery-beat' -c "$PWD" "${VENV_CMD}celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"

# Create a window for Stripe CLI
tmux new-window -n 'stripe-cli' -c "$PWD" "stripe listen --forward-to localhost:$PORT/payments/webhook/"

# Create a window for Localtunnel
tmux new-window -n 'localtunnel' -c "$PWD" "npx localtunnel --port $PORT --subdomain fastjob"

# Set focus to the first window (django)
tmux select-window -t $SESSION_NAME:0

echo "Session created on port $PORT. You can attach to it using: tmux attach -t $SESSION_NAME"
