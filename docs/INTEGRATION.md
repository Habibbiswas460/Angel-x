# Integration Steps

Step-by-step setup to connect Angel-X to your AngelOne account and start the stack.

## Prerequisites
- AngelOne SmartAPI credentials (client ID, API key)
- Docker + docker-compose
- Optional: Python 3.12+ if you plan to run locally instead of Docker

## Configure Broker and App
1. Copy the production config and edit credentials:
```bash
cp config/config.production.py config/config.py
# open config/config.py and set ANGELONE_CLIENT_ID, ANGELONE_API_KEY, DB credentials
```
2. (Optional) Set environment variables if you prefer env-based secrets:
```
ANGELONE_CLIENT_ID=...
ANGELONE_API_KEY=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
```
3. (Optional) Add sample tick data to `ticks/` (e.g., `ticks_20260109.csv`) to enable faster ML signal generation.

## Bring Up the Stack (Docker)
```bash
sudo docker-compose up -d --build
sudo docker-compose ps
curl http://localhost:5000/health
```

## Verify
- Dashboard/API: http://localhost:5000
- Health: http://localhost:5000/health
- Common data endpoints: `/api/dashboard`, `/api/positions`, `/api/portfolio`, `/api/market`, `/api/performance`, `/api/trades`, `/api/greeks-heatmap`

## Optional ML Extras
- `scikit-learn` is preinstalled in the image.
- For full deep-learning/backtesting variants, uncomment in `requirements.txt` and rebuild:
  - `tensorflow-cpu>=2.12.0`
  - `xgboost>=1.7.6`
- ML integration lives in `src/ml/integration.py` and is wired in `src/integration_hub.py` with safe fallbacks.

## Local (non-Docker) Workflow
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Run tests locally:
```bash
pip install -r requirements-test.txt
pytest tests -q --tb=short
```
