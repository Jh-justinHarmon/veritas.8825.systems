FROM node:22-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.9.6 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt
FROM python:3.9.6-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
COPY --from=frontend-builder /frontend/dist frontend/dist
CMD ["/app/.venv/bin/flask", "run", "--host=0.0.0.0", "--port=8080"]
