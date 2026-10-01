# Runtime and Container Spec

## CURRENT

- The project runs as a Python 3.11+ CLI and stores serving data in SQLite.
- The `budongi` container runs that same CLI as a non-root user. SQLite files, evaluation logs, and reports persist in mounted project folders.
- The optional `llm` Compose profile runs the pinned Ollama image on the private Compose network. The Ollama port is not published on the host.
- The default `budongi` service does not allow Docker service hostnames. Only the separate `budongi-llm` service, in the `llm` profile and with a dependency on the actual Ollama service, sets `BUDONGI_ALLOW_DOCKER_OLLAMA=1` and uses its internal hostname.
- Data ingestion, database technology, Tool contracts, and the public interface do not change as part of containerization.

## Run contract

- Build/run with Docker Compose from this project directory.
- The default service is a one-shot CLI container. Commands and exit status are passed through unchanged.
- `data/`, `runs/`, `tool_runs/`, and `reports/` are mounted from the project directory so their contents survive container removal.
- Ollama is opt-in through the `llm` profile; its model files persist in the named `ollama_models` volume. Use `budongi-llm` for model-backed CLI commands.
- No HTTP API service is provided by this spec. A future API, worker, or external data adapter needs its own interface and spec before being added.

## Acceptance criteria

- `docker compose build budongi` builds the CLI image.
- `docker compose run --rm budongi init-db` creates the SQLite schema in the mounted historical data directory.
- `docker compose --profile llm up -d ollama` starts Ollama without publishing its port to the host.
- The base app rejects the `ollama` hostname. The opt-in `budongi-llm` app can reach its Compose Ollama dependency; other non-loopback hosts remain rejected.
- Removing the app container does not remove database, log, report, or Ollama model files.

## TARGET / OPEN QUESTION

- Add HTTP services or split storage/tools only when a confirmed product interface or measured operational need requires them.
- GPU passthrough and Windows/WSL-specific performance tuning are environment-specific follow-up work; the base profile is CPU-compatible.
