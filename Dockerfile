FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .
RUN uv sync --frozen

EXPOSE 8080
CMD ["uv", "run", "devui", "--host", "0.0.0.0", "--port", "8080"]
