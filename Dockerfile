FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system gateway && useradd --system --gid gateway gateway
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway ./gateway

USER gateway
EXPOSE 8787

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8787", "--no-access-log"]

