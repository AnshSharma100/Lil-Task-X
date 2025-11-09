# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY client ./client
COPY README.md ./README.md

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
