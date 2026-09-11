# Built with repo root as build context (see docker-compose.yml) so this
# can install shared/ alongside its own requirements.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-dev.txt ./
COPY agents/dashboard_agent/requirements.txt ./agents/dashboard_agent/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt -r agents/dashboard_agent/requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "agents.dashboard_agent.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
