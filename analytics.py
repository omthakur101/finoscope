from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def portfolio_returns(prices: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    returns = prices.pct_change().dropna()
    cols = [t for t in weights if t in returns.columns]
    if not cols:
        return pd.Series(dtype=float)
    w = np.array([weights[t] for t in cols], dtype=float)
    w = w / w.sum()
    return returns[cols].dot(w)


def portfolio_metrics(prices: pd.DataFrame, weights: dict[str, float]) -> dict:
    r = portfolio_returns(prices, weights)
    if r.empty:
        return {}
    cumulative = (1 + r).cumprod()
    annual_return = float(cumulative.iloc[-1] ** (252 / len(r)) - 1)
    volatility = float(r.std() * np.sqrt(252))
    sharpe = float((r.mean() / r.std()) * np.sqrt(252)) if r.std() else 0.0
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = float(drawdown.min())
    var95 = float(np.quantile(r, 0.05))
    return {
        "annual_return": annual_return,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "var_95_daily": var95,
        "observations": int(len(r)),
    }


def monte_carlo_var(prices: pd.DataFrame, weights: dict[str, float], simulations: int = 5000) -> float:
    r = portfolio_returns(prices, weights)
    if r.empty:
        return 0.0
    mu, sigma = float(r.mean()), float(r.std())
    rng = np.random.default_rng(42)
    simulated = rng.normal(mu, sigma, simulations)
    return float(np.quantile(simulated, 0.05))


def detect_anomalies(prices: pd.DataFrame, ticker: str) -> list[dict]:
    if ticker not in prices:
        return []
    s = prices[ticker].pct_change().dropna()
    if len(s) < 30:
        return []
    features = pd.DataFrame({
        "return": s,
        "volume_proxy": s.abs().rolling(5).mean().fillna(s.abs()),
        "volatility": s.rolling(10).std().fillna(s.std()),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    model = IsolationForest(contamination=0.03, random_state=42)
    labels = model.fit_predict(features)
    scores = -model.score_samples(features)
    out = []
    for idx, label, score in zip(features.index, labels, scores):
        if label == -1:
            out.append({"date": str(idx.date()), "return": float(s.loc[idx]), "score": float(score)})
    return out[-10:]


def backtest_momentum(prices: pd.DataFrame, ticker: str, lookback: int = 20) -> dict:
    s = prices[ticker].dropna()
    if len(s) < lookback + 5:
        return {}
    daily = s.pct_change().fillna(0)
    signal = (s > s.rolling(lookback).mean()).astype(float).shift(1).fillna(0)
    strategy = signal * daily
    equity = (1 + strategy).cumprod()
    benchmark = (1 + daily).cumprod()
    running = equity.cummax()
    dd = equity / running - 1
    return {
        "ticker": ticker,
        "strategy_return": float(equity.iloc[-1] - 1),
        "benchmark_return": float(benchmark.iloc[-1] - 1),
        "max_drawdown": float(dd.min()),
        "trades": int(signal.diff().abs().sum()),
    }
