# Built with repo root as build context (see docker-compose.yml) so this
# can install shared/ alongside its own requirements.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-dev.txt ./
COPY orchestrator/requirements.txt ./orchestrator/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt -r orchestrator/requirements.txt

COPY . .

# TODO (owner): replace with the real entrypoint once run_pipeline() is
# implemented (e.g. `CMD ["python", "-m", "orchestrator.orchestrator"]` or an
# API server). Idles for now so `docker-compose up` can bring the topology up
# before there's real logic to run.
CMD ["sleep", "infinity"]
