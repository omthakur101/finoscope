from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analytics import portfolio_metrics, monte_carlo_var, detect_anomalies, backtest_momentum

BASE = Path(__file__).parent
app = FastAPI(title="FinOScope", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY"]


def make_demo_prices(days: int = 420) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    starts = {"AAPL": 180, "MSFT": 420, "NVDA": 140, "AMZN": 190, "GOOGL": 175, "SPY": 550}
    frames = {}
    for ticker, start in starts.items():
        drift = 0.00035 + rng.normal(0, 0.0001)
        shocks = rng.normal(drift, 0.018 if ticker != "SPY" else 0.010, len(dates))
        frames[ticker] = start * np.exp(np.cumsum(shocks))
    return pd.DataFrame(frames, index=dates)

PRICES = make_demo_prices()

class Holding(BaseModel):
    ticker: str = Field(min_length=1, max_length=6)
    shares: float = Field(gt=0)

class PortfolioRequest(BaseModel):
    holdings: list[Holding]


def weights_from_holdings(holdings: list[Holding]) -> dict[str, float]:
    values = {}
    for h in holdings:
        ticker = h.ticker.upper()
        if ticker not in PRICES.columns:
            raise HTTPException(400, f"Unsupported demo ticker: {ticker}")
        values[ticker] = values.get(ticker, 0) + h.shares * float(PRICES[ticker].iloc[-1])
    total = sum(values.values())
    return {k: v / total for k, v in values.items()}

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/market")
def market():
    result = []
    for ticker in TICKERS:
        s = PRICES[ticker]
        result.append({
            "ticker": ticker,
            "price": round(float(s.iloc[-1]), 2),
            "change": round(float(s.iloc[-1] / s.iloc[-2] - 1), 4),
        })
    return {"data_source": "deterministic demo market data", "items": result}

@app.post("/api/portfolio")
def portfolio(req: PortfolioRequest):
    weights = weights_from_holdings(req.holdings)
    metrics = portfolio_metrics(PRICES, weights)
    metrics["monte_carlo_var_95"] = monte_carlo_var(PRICES, weights)
    return {"weights": weights, "metrics": metrics}

@app.get("/api/anomalies/{ticker}")
def anomalies(ticker: str):
    ticker = ticker.upper()
    if ticker not in PRICES.columns:
        raise HTTPException(404, "Ticker not available")
    return {"ticker": ticker, "anomalies": detect_anomalies(PRICES, ticker)}

@app.get("/api/backtest/{ticker}")
def backtest(ticker: str):
    ticker = ticker.upper()
    if ticker not in PRICES.columns:
        raise HTTPException(404, "Ticker not available")
    return backtest_momentum(PRICES, ticker)

@app.get("/api/history/{ticker}")
def history(ticker: str):
    ticker = ticker.upper()
    if ticker not in PRICES.columns:
        raise HTTPException(404, "Ticker not available")
    s = PRICES[ticker].tail(90)
    return {"ticker": ticker, "data": [{"date": str(i.date()), "price": round(float(v), 2)} for i, v in s.items()]}
