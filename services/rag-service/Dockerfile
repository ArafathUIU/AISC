FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS development
COPY services/rag-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils
COPY services/rag-service/rag_service/ /app/rag_service/
ENV PYTHONPATH=/app
CMD ["uvicorn", "rag_service.main:app", "--host", "0.0.0.0", "--port", "8006", "--reload"]

FROM base AS production
COPY services/rag-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils
COPY services/rag-service/rag_service/ /app/rag_service/
ENV PYTHONPATH=/app
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8006/health || exit 1
CMD ["gunicorn", "rag_service.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8006"]
