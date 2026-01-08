# fit-buddy-data
This project aims to study gym traffic. How to predict if the bench will be available for you this Thursday at 1pm?

## Run the project

### Development mode

Requires `uv` installed:

```bash
cd .../fit-buddy-data 
uv sync 
uv run dev
```

API runs on `http://localhost:8000/`

### Docker mode

```bash
docker compose up
```

API runs on `http://localhost:8080/`

## Endpoints

### Health check
```
GET /
```

### Machine prediction
```
GET /api/machine/{machine_id}/prediction
```

Example: Check current machine availability
```bash
curl -X GET "http://localhost:8080/api/machine/DC_BENCH_001/prediction"
```

For detailed documentation, see [API_PREDICTION.md](data/Documentation%20pour%20d%C3%A9veloppement/API_PREDICTION.md)

> Note: DB connection errors are normal if the database isn't configured.