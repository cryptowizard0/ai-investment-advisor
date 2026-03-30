# Container Runtime

Build script:

```bash
sh apps/build-container.sh
```

Run script:

```bash
sh apps/run-container.sh
```

Background run:

```bash
DETACH=1 sh apps/run-container.sh
```

Services:

- Web: `http://localhost:3000`
- Backend: `http://localhost:8000/healthz`
- Agent: `http://localhost:9002/healthz`

This container starts all three layers in one process group for local development and demo use.

Entrypoint script:

- `/app/apps/start-entrypoint.sh`

Python dependencies are installed into an internal virtual environment at `/opt/venv` inside the image to avoid Debian's externally-managed Python restriction.
