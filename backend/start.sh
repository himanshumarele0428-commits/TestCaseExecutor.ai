#!/usr/bin/env bash
set -e

# Virtual display for headed Chromium.
if ! pgrep -x Xvfb > /dev/null; then
  Xvfb :99 -screen 0 1280x720x24 -nolisten tcp &
fi

# Wait for the X server to be ready.
for _ in $(seq 1 30); do
  if xdpyinfo -display :99 > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# VNC server exposing the virtual display (no password, loopback-only).
x11vnc -display :99 -forever -shared -nopw -localhost -rfbport 5900 &

# noVNC websockify proxy bridges browser WebSocket -> localhost:5900.
python3 -m websockify --web /opt/novnc 6080 localhost:5900 &

exec uvicorn playwright_service.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
