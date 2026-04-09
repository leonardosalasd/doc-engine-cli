FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY doc_engine/ ./doc_engine/

RUN pip install --no-cache-dir .

WORKDIR /workspace

ENTRYPOINT ["python", "-m", "doc_engine"]

CMD ["build"]
