# Built with repo root as build context (see docker-compose.yml) so this
# can install shared/ alongside its own requirements.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-dev.txt ./
COPY agents/dashboard_agent/requirements.txt ./agents/dashboard_agent/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt -r agents/dashboard_agent/requirements.txt

COPY . .

EXPOSE 8501

# TODO (owner): switch to `CMD ["streamlit", "run", "agents/dashboard_agent/app.py",
# "--server.address=0.0.0.0"]` once app.py's main() is implemented (it
# currently raises NotImplementedError). Idles for now so the container
# starts cleanly.
CMD ["sleep", "infinity"]
