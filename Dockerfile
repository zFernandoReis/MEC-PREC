FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    TZ=America/Sao_Paulo

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home app

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY tests ./tests
COPY dados ./dados
RUN uv sync --frozen --no-editable

USER app
EXPOSE 8000
CMD ["python", "-m", "app.bootstrap.start_server"]
