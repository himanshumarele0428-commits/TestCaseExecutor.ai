FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

COPY playwright_service/ /app/playwright_service/
COPY app/ /app/app/
COPY requirements-railway.txt /app/

RUN pip install --no-cache-dir -r requirements-railway.txt
RUN playwright install chromium --with-deps

ENV SCREENSHOTS_DIR=/app/screenshots
RUN mkdir -p /app/screenshots

EXPOSE 8000

CMD ["sh", "-c", "uvicorn playwright_service.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
