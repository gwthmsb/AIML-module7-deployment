# Run Backend and Frontend

## Prerequisites

- Docker and Docker Compose installed and running.
- These images available locally:
  - `mccombs-mod7-backend:latest`
  - `mccombs-mod7-frontend:latest`

## Start the Services

From the directory containing `docker-compose.yml`, run:

```bash
docker compose up -d
```

Access the services:

- Frontend: http://localhost:8501
- Backend: http://localhost:7860

The frontend connects to the backend using `http://backend:7860` over the shared Docker network.

## Check Status and Logs

```bash
docker compose ps
docker compose logs -f
```

Press `Ctrl+C` to exit the logs; the containers keep running.

## Stop the Services

```bash
docker compose down
```
