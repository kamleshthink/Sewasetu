FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Set working directory to app
WORKDIR /app/app

RUN mkdir -p /var/sewasetu/uploads /var/log/sewasetu \
    && crontab /app/app/deploy/crontab

ENV PORT=8000
EXPOSE 8000

CMD sh -c "cron && gunicorn --bind 0.0.0.0:${PORT} --workers 4 --timeout 30 app:app"
