from fastapi.testclient import TestClient

from backend.app.deriv.service import DerivBotService, DerivRequest, analyze_prices
from backend.app.main import app


def test_random_analysis_returns_explainable_features():
    prices = [100 + index * 0.2 + ((index % 4) - 1.5) * 0.1 for index in range(30)]
    result = analyze_prices(prices)
    assert {"hurst_exponent", "z_score", "entropy", "regime"} <= result.keys()
    assert 0 <= result["hurst_exponent"] <= 1


def test_risk_gate_rejects_hold_or_excessive_losses():
    prices = [100 + (index % 2) * 0.01 for index in range(30)]
    result = DerivBotService().plan(DerivRequest(), prices, losses=2)
    assert result["risk"]["allowed"] is False


def test_deriv_api_exposes_strategy_catalog():
    response = TestClient(app).get("/api/deriv/strategies")
    assert response.status_code == 200
    assert "martingale" in response.json()["strategies"]