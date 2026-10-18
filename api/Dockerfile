FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system app && \
    adduser --system --ingroup app app

COPY . .

EXPOSE 42000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:42000/health')"]

USER app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "42000"]
