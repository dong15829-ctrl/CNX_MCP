# DI_ES Dashboard Backend (FastAPI)

## Quickstart (local)

1) Start MySQL (from repo root)

```bash
docker compose -f DI_ES_Dashboard/docker-compose.yml up -d mysql
```

2) Create a Python venv + install deps

```bash
cd DI_ES_Dashboard/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3) Configure env

```bash
cp .env.example .env
```

4) Init DB schema

```bash
python3 -m di_es_dashboard_api.scripts.init_db
```

5) Run API

```bash
uvicorn di_es_dashboard_api.main:app --reload --app-dir src --port 8000
```

Open: `http://localhost:8000/api/health`

## Notes

- Upload endpoint: `POST /api/admin/uploads` (multipart form field name: `file`)
- Queries use the latest **completed** upload for a given period/type.

