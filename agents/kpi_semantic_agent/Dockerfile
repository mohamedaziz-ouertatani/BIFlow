# Built with repo root as build context (see docker-compose.yml) so this
# can install shared/ alongside its own requirements.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-dev.txt ./
COPY agents/kpi_semantic_agent/requirements.txt ./agents/kpi_semantic_agent/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt -r agents/kpi_semantic_agent/requirements.txt

COPY . .

# Intentionally idle: agents are library modules, not servers. The pipeline runs
# in-process inside the dashboard_agent container (GET /api/pipeline/run
# imports the orchestrator, which imports every agent). This container just
# stays up so you can `docker compose exec <service> pytest`.
CMD ["sleep", "infinity"]
