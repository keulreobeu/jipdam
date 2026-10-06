# Runtime and Container Spec

## CURRENT

- The project runs as a Python 3.11+ CLI and stores serving data in SQLite.
- `rental-demo` prepares fictional data. `recommend --rental-db ... --snapshot-id ... --request ... --allow-synthetic` reads a sealed rental_v1 snapshot without a model or provider calls; the rental DB is opened read-only and independently of the global historical --db argument.
- `jipdam credentials` starts a Windows-only, loopback HTTP settings page for the encrypted API credential vault. It stores credential ciphertext outside the project under `%LOCALAPPDATA%\Jipdam\` and protects the AES key with Windows Credential Manager.
- The `budongi` container runs that same CLI as a non-root user. SQLite files, evaluation logs, and reports persist in mounted project folders.
- The optional `llm` Compose profile runs the pinned Ollama image on the private Compose network. The Ollama port is not published on the host.
- The default `budongi` service does not allow Docker service hostnames. Only the separate `budongi-llm` service, in the `llm` profile and with a dependency on the actual Ollama service, sets `BUDONGI_ALLOW_DOCKER_OLLAMA=1` and uses its internal hostname.
- Data ingestion, database technology, Tool contracts, and the public interface do not change as part of containerization.

## Run contract

- Build/run with Docker Compose from this project directory.
- The default service is a one-shot CLI container. Commands and exit status are passed through unchanged.
- `data/`, `runs/`, `tool_runs/`, and `reports/` are mounted from the project directory so their contents survive container removal.
- Ollama is opt-in through the `llm` profile; its model files persist in the named `ollama_models` volume. Use `budongi-llm` for model-backed CLI commands.
- The credentials settings service is separate from the Docker one-shot CLI; it is not exposed by Compose and does not bind to a non-loopback address.
- CURRENT: The credential vault settings API exists; the rental recommendation HTTP endpoint is still a TARGET defined by [RENT-001](10_rental_recommendation_spec.md).

## Acceptance criteria

- `docker compose build budongi` builds the CLI image.
- `docker compose run --rm budongi init-db` creates the SQLite schema in the mounted historical data directory.
- `docker compose --profile llm up -d ollama` starts Ollama without publishing its port to the host.
- The base app rejects the `ollama` hostname. The opt-in `budongi-llm` app can reach its Compose Ollama dependency; other non-loopback hosts remain rejected.
- Removing the app container does not remove database, log, report, or Ollama model files.
- On Windows, `jipdam credentials` binds only to `127.0.0.1`, rejects untrusted Host/Origin/CSRF requests, and never returns stored API key values.

## TARGET / OPEN QUESTION

- TARGET: [RENT-001](10_rental_recommendation_spec.md) adds POST /api/recommendations and a local comparison page; this rental endpoint remains unimplemented. [CRED-001](11_api_credential_vault_spec.md) is implemented as a separate settings page/API for folders and API key aliases. It stores authenticated ciphertext outside the project data directories; Windows Credential Manager protects the encryption key, and unsupported secure storage fails closed. The API key value is submitted once to the server but never returned, persisted in browser storage, sent to the LLM, or written to logs. No separate frontend build, chat session, map, external deployment, or current Compose change is included.
- TARGET: latest rental raw/normalized/serving files live separately under data/rental/; the existing historical DB, importer cutoff and CLI Compose runtime remain unchanged.
- GPU passthrough and Windows/WSL-specific performance tuning are environment-specific follow-up work; the base profile is CPU-compatible.
