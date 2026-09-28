from app import PRICES
from analytics import portfolio_metrics, monte_carlo_var


def test_metrics_exist():
    result = portfolio_metrics(PRICES, {"AAPL": 0.5, "SPY": 0.5})
    assert "volatility" in result
    assert result["observations"] > 100


def test_weights_are_reasonable():
    result = portfolio_metrics(PRICES, {"AAPL": 1.0})
    assert -1 < result["max_drawdown"] <= 0


def test_monte_carlo_is_number():
    value = monte_carlo_var(PRICES, {"AAPL": 1.0}, simulations=1000)
    assert isinstance(value, float)
