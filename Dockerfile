FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TMPDIR=/work \
    HF_HOME=/work/hf \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN pip install --no-cache-dir "uv==0.12.12" \
    && uv sync --locked --no-dev

RUN useradd --create-home --uid 10001 appuser
USER 10001:10001

ENTRYPOINT ["cmdp-consumer"]
