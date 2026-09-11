# Built with repo root as build context (see docker-compose.yml) so this
# can install shared/ alongside its own requirements.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-dev.txt ./
COPY agents/data_engineering_agent/requirements.txt ./agents/data_engineering_agent/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt -r agents/data_engineering_agent/requirements.txt

COPY . .

# TODO (owner): replace with the real entrypoint once agent.py is implemented.
CMD ["sleep", "infinity"]
