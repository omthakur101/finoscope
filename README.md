# FinOScope

FinOScope is an AI-ready financial risk and market intelligence MVP. It demonstrates portfolio analytics, risk measurement, anomaly detection, systematic backtesting, a REST API, automated tests, and a browser dashboard.

## Current MVP
- FastAPI REST backend
- Portfolio analytics: annualized return, volatility, Sharpe ratio, maximum drawdown
- Historical and Monte Carlo-style daily VaR
- Isolation Forest anomaly detection
- Momentum strategy backtesting
- Responsive browser dashboard
- Automated pytest tests
- No paid API keys required: deterministic demo market data is used

## Run locally

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

## Important
The market data included in this MVP is synthetic/deterministic demo data. It is intentionally labeled as such. A production version should use a licensed real-time/historical market-data provider and should add authentication, persistent storage, monitoring, rate limiting, and production deployment.

## Architecture
Browser → FastAPI → Analytics/Risk/ML services → data provider/database.
