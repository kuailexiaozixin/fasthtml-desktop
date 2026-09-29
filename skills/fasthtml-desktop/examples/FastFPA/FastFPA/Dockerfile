FROM python:3.12-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FASTFPA_ENV=production
ENV FASTFPA_PORT=5018
ENV FASTFPA_DB=/data/fastfpa.sqlite
EXPOSE 5018
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://127.0.0.1:5018/healthz || exit 1
CMD ["python", "web_app.py"]
