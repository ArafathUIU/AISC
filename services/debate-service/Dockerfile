FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS development
COPY services/debate-service/requirements.txt services/debate-service/requirements.txt 2>/dev/null || true
RUN pip install fastapi uvicorn pydantic pydantic-settings
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils
COPY services/debate-service/debate_service/ /app/debate_service/
ENV PYTHONPATH=/app
CMD ["uvicorn", "debate_service.main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]

FROM base AS production
RUN pip install fastapi uvicorn gunicorn pydantic pydantic-settings
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils
COPY services/debate-service/debate_service/ /app/debate_service/
ENV PYTHONPATH=/app
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8010/health || exit 1
CMD ["gunicorn", "debate_service.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8010"]
