FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV DEBIAN_FRONTEND=noninteractive

# Xvfb provides a virtual display, x11vnc exposes it over VNC,
# git fetches noVNC which streams that VNC session to a browser.
RUN apt-get update && apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        x11-utils \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch v1.3.0 https://github.com/novnc/noVNC.git /opt/novnc \
    && rm -rf /opt/novnc/.git

WORKDIR /app

COPY playwright_service/ /app/playwright_service/
COPY app/ /app/app/
COPY requirements-railway.txt /app/
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh
RUN pip install --no-cache-dir -r requirements-railway.txt
RUN playwright install chromium --with-deps

ENV SCREENSHOTS_DIR=/app/screenshots
ENV DISPLAY=:99
RUN mkdir -p /app/screenshots

EXPOSE 8000

CMD ["/app/start.sh"]
