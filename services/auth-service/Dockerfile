FROM python:3.12-slim AS base

WORKDIR /app

FROM base AS development
COPY services/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models && pip install -e /app/libs/aisc-utils
COPY services/auth-service/src/ /app/src/
ENV PYTHONPATH=/app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

FROM base AS production
COPY services/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models && pip install -e /app/libs/aisc-utils
COPY services/auth-service/src/ /app/src/
ENV PYTHONPATH=/app
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8001/health || exit 1
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]
