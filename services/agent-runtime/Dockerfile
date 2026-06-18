FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS development
COPY services/agent-runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils -e /app/libs/aisc-events
COPY services/agent-runtime/agent_runtime/ /app/agent_runtime/
ENV PYTHONPATH=/app
CMD ["uvicorn", "agent_runtime.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

FROM base AS production
COPY services/agent-runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY libs/ /app/libs/
RUN pip install -e /app/libs/aisc-models -e /app/libs/aisc-utils -e /app/libs/aisc-events
COPY services/agent-runtime/agent_runtime/ /app/agent_runtime/
ENV PYTHONPATH=/app
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8003/health || exit 1
CMD ["gunicorn", "agent_runtime.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8003"]
