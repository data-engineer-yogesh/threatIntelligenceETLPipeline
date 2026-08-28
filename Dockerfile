FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion/ ingestion/
COPY bronze/ bronze/
COPY silver/ silver/
COPY enrichment/ enrichment/
COPY gold/ gold/
COPY main.py .

RUN mkdir -p data/raw data/bronze

CMD ["python", "main.py"]