#!/bin/bash

SESSION_NAME="fastjob_dev"

# 1. ATTACH IF EXISTS
# If the session already exists, just attach and exit the script
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

# 2. CLEANUP & INITIALIZATION
# Only runs if the session does NOT exist
echo "Creating new dev session: $SESSION_NAME"
pkill -f portless 2>/dev/null

echo "Initializing Portless..."
portless proxy start
portless trust

# 3. DYNAMIC PORT SELECTION
PORT=8000
while ss -tuln | grep -q ":$PORT " ; do
    PORT=$((PORT+1))
done
echo "Using available port: $PORT"

# 4. VIRTUAL ENV DETECTION
# Checks for your preferred venv folders
VENV_CMD=""
if [ -d "venv" ]; then
    VENV_CMD="source venv/bin/activate && "
elif [ -d ".venv" ]; then
    VENV_CMD="source .venv/bin/activate && "
fi

# 5. CREATE TMUX SESSION
# First window: Django managed by Portless
tmux new-session -d -s $SESSION_NAME -n 'django-portless' -c "$PWD" \
    "bash -c '${VENV_CMD}portless fastjob --app-port $PORT -- python manage.py runserver $PORT; read'"

# Second window: Celery Worker
tmux new-window -n 'celery-worker' -c "$PWD" \
    "bash -c '${VENV_CMD}celery -A config worker -l info -c 4; read'"

# Third window: Celery Beat
tmux new-window -n 'celery-beat' -c "$PWD" \
    "bash -c '${VENV_CMD}celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler; read'"

# Fourth window: Stripe CLI
tmux new-window -n 'stripe-cli' -c "$PWD" \
    "bash -c 'stripe listen --forward-to localhost:$PORT/payments/webhook/; read'"

# 6. FINAL SETUP
# Focus on the first window and attach
tmux select-window -t $SESSION_NAME:0
echo "----------------------------------------------------"
echo "Session created successfully!"
echo "URL: https://fastjob.localhost"
echo "----------------------------------------------------"

tmux attach -t $SESSION_NAME
