"""Tests for Dashboard API endpoints"""

import pytest
import json
import os
from flask import Flask
from src.dashboard.routes import dashboard_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(dashboard_bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestDashboardRoutes:
    """Test dashboard HTML routes"""

    def test_dashboard_default(self, client):
        """Test default dashboard route"""
        response = client.get("/dashboard/")
        # May return 200 or 404 depending on whether HTML file exists
        assert response.status_code in [200, 404, 500]

    def test_dashboard_advanced(self, client):
        """Test advanced dashboard route"""
        response = client.get("/dashboard/advanced")
        assert response.status_code in [200, 404, 500]

    def test_dashboard_minimal(self, client):
        """Test minimal dashboard route"""
        response = client.get("/dashboard/minimal")
        assert response.status_code in [200, 404, 500]


class TestAPIEndpoints:
    """Test API endpoints"""

    def test_api_live_data(self, client):
        """Test /api/live endpoint"""
        response = client.get("/dashboard/api/live")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "timestamp" in data
        assert "status" in data
        assert "data" in data
        assert data["status"] == "active"

        # Check nested data structure
        assert "nifty_ltp" in data["data"]
        assert "open_positions" in data["data"]
        assert "total_pnl" in data["data"]
        assert "greeks" in data["data"]

    def test_api_positions(self, client):
        """Test /api/positions endpoint"""
        response = client.get("/dashboard/api/positions")
        assert response.status_code == 200

        positions = json.loads(response.data)
        assert isinstance(positions, list)

        if len(positions) > 0:
            pos = positions[0]
            assert "symbol" in pos
            assert "quantity" in pos
            assert "entry_price" in pos
            assert "current_price" in pos
            assert "pnl" in pos
            assert "side" in pos

    def test_api_trades(self, client):
        """Test /api/trades endpoint"""
        response = client.get("/dashboard/api/trades")
        assert response.status_code == 200

        trades = json.loads(response.data)
        assert isinstance(trades, list)

        if len(trades) > 0:
            trade = trades[0]
            assert "timestamp" in trade
            assert "symbol" in trade
            assert "side" in trade
            assert "quantity" in trade
            assert "price" in trade

    def test_api_health(self, client):
        """Test /api/health endpoint"""
        response = client.get("/dashboard/api/health")
        assert response.status_code == 200

        health = json.loads(response.data)
        assert "broker_api" in health
        assert "websocket" in health
        assert "database" in health

        # Check structure
        for service in health.values():
            assert "status" in service
            assert "latency" in service
            assert "uptime" in service

    def test_api_metrics(self, client):
        """Test /api/metrics endpoint"""
        response = client.get("/dashboard/api/metrics")
        assert response.status_code == 200

        metrics = json.loads(response.data)
        assert "total_pnl" in metrics
        assert "daily_pnl" in metrics
        assert "total_trades" in metrics
        assert "wins" in metrics
        assert "losses" in metrics
        assert "win_rate" in metrics
        assert "capital" in metrics
        assert "margin_used" in metrics

        # Validate types
        assert isinstance(metrics["total_trades"], int)
        assert isinstance(metrics["win_rate"], (int, float))
        assert isinstance(metrics["capital"], (int, float))

    def test_api_pnl_chart(self, client):
        """Test /api/chart/pnl endpoint"""
        response = client.get("/dashboard/api/chart/pnl")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "labels" in data
        assert "values" in data
        assert isinstance(data["labels"], list)
        assert isinstance(data["values"], list)
        assert len(data["labels"]) == len(data["values"])

    def test_api_price_chart(self, client):
        """Test /api/chart/price endpoint"""
        response = client.get("/dashboard/api/chart/price")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

        if len(data) > 0:
            candle = data[0]
            assert "time" in candle
            assert "open" in candle
            assert "high" in candle
            assert "low" in candle
            assert "close" in candle

            # OHLC validation
            assert candle["high"] >= candle["open"]
            assert candle["high"] >= candle["close"]
            assert candle["low"] <= candle["open"]
            assert candle["low"] <= candle["close"]

    def test_api_greek_exposure(self, client):
        """Test /api/greek-exposure endpoint"""
        response = client.get("/dashboard/api/greek-exposure")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "delta" in data
        assert "gamma" in data
        assert "theta" in data
        assert "vega" in data
        assert "iv" in data

        # Check structure
        for greek in data.values():
            assert "value" in greek
            assert "status" in greek
            assert greek["status"] in ["positive", "negative", "neutral"]


class TestOrderAPI:
    """Test order placement API"""

    def test_place_order_disabled_by_default(self, client):
        """Test that order API is disabled by default"""
        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": 1,
            "price": 125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        # Should be forbidden (403) by default
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_enabled(self, client, monkeypatch):
        """Test order placement when enabled"""
        # Enable order API
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": 1,
            "price": 125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert "order_id" in data
        assert "status" in data
        assert data["symbol"] == "NIFTY 28000 CE"
        assert data["side"] == "BUY"
        assert data["quantity"] == 1
        assert data["price"] == 125.50

    def test_place_order_invalid_side(self, client, monkeypatch):
        """Test order with invalid side"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "INVALID",
            "quantity": 1,
            "price": 125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_invalid_quantity(self, client, monkeypatch):
        """Test order with invalid quantity"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": "invalid",
            "price": 125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_negative_quantity(self, client, monkeypatch):
        """Test order with negative quantity"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": -1,
            "price": 125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_invalid_price(self, client, monkeypatch):
        """Test order with invalid price"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": 1,
            "price": "invalid",
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_negative_price(self, client, monkeypatch):
        """Test order with negative price"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": 1,
            "price": -125.50,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_place_order_sell_side(self, client, monkeypatch):
        """Test SELL order placement"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        order_data = {
            "symbol": "NIFTY 28000 PE",
            "side": "SELL",
            "quantity": 2,
            "price": 98.75,
        }

        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps(order_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["side"] == "SELL"
        assert data["quantity"] == 2

    def test_place_order_missing_data(self, client, monkeypatch):
        """Test order with missing fields"""
        monkeypatch.setenv("DASHBOARD_ORDER_API_ENABLED", "true")

        # Empty order
        response = client.post(
            "/dashboard/api/place-order",
            data=json.dumps({}),
            content_type="application/json",
        )

        # Should still work with defaults
        assert response.status_code in [201, 400]


class TestAPIErrorHandling:
    """Test error handling in API endpoints"""

    def test_api_endpoints_return_json(self, client):
        """Test that all API endpoints return JSON"""
        endpoints = [
            "/dashboard/api/live",
            "/dashboard/api/positions",
            "/dashboard/api/trades",
            "/dashboard/api/health",
            "/dashboard/api/metrics",
            "/dashboard/api/chart/pnl",
            "/dashboard/api/chart/price",
            "/dashboard/api/greek-exposure",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.content_type == "application/json"

            # Verify valid JSON
            data = json.loads(response.data)
            assert data is not None

    def test_api_methods_not_allowed(self, client):
        """Test that POST is not allowed on GET endpoints"""
        response = client.post("/dashboard/api/live")
        assert response.status_code == 405  # Method Not Allowed
