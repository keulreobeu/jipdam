FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir . \
    && groupadd --system budongi \
    && useradd --system --gid budongi --home-dir /app --no-create-home budongi \
    && mkdir -p /app/data/historical /app/runs /app/tool_runs /app/reports \
    && chown -R budongi:budongi /app

USER budongi

ENTRYPOINT ["budongi"]
