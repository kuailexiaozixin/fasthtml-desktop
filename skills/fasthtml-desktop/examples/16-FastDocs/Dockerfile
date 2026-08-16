FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FASTDOCS_DB=/data/fastdocs.sqlite
ENV FASTDOCS_PORT=5016
EXPOSE 5016
CMD ["sh", "-c", "python -c 'import db,seed; seed.build() if not db.db_exists() else None' && python web_app.py"]
