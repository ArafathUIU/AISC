FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS development
COPY services/memory-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models && pip install -e /app/libs/aisc-utils
COPY services/memory-service/memory_service/ /app/memory_service/
ENV PYTHONPATH=/app
CMD ["uvicorn", "memory_service.main:app", "--host", "0.0.0.0", "--port", "8007", "--reload"]

FROM base AS production
COPY services/memory-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models && pip install -e /app/libs/aisc-utils
COPY services/memory-service/memory_service/ /app/memory_service/
ENV PYTHONPATH=/app
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8007/health || exit 1
CMD ["gunicorn", "memory_service.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8007"]
