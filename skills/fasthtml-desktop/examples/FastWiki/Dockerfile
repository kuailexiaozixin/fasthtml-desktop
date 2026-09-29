FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/uploads
ENV FASTWIKI_ENV=production FASTWIKI_PORT=5022 FASTWIKI_DB=/app/data/fastwiki.sqlite FASTWIKI_UPLOAD_DIR=/app/data/uploads
EXPOSE 5022
CMD ["python", "app.py"]

