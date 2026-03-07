def register_user(client, email, password, name):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "name": name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client, email, password):
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_base_resources(client, token, symbol="EURUSD"):
    portfolio = client.post(
        "/portfolios/",
        json={
            "name": f"Portfolio Metrics {symbol}",
            "description": "portfolio metrics test",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": f"Cuenta Metrics {symbol}",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": f"Strategy {symbol}",
            "symbol": symbol,
            "timeframe": "H1",
            "risk_percent": 1.5,
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text
    strategy_id = strategy.json()["id"]

    return {
        "portfolio_id": portfolio_id,
        "broker_id": broker_id,
        "strategy_id": strategy_id,
    }


def create_trade(client, token, strategy_id, broker_account_id, symbol="EURUSD", side="buy"):
    response = client.post(
        "/trades/",
        json={
            "symbol": symbol,
            "side": side,
            "volume": 0.10,
            "entry_price": 1.1000,
            "exit_price": None,
            "stop_loss": 1.0900,
            "take_profit": 1.1200,
            "status": "open",
            "pnl": None,
            "strategy_id": strategy_id,
            "broker_account_id": broker_account_id,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def close_trade(client, token, trade_id, pnl, exit_price=1.1050):
    response = client.patch(
        f"/trades/{trade_id}",
        json={
            "status": "closed",
            "pnl": pnl,
            "exit_price": exit_price,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_metrics_summary_returns_expected_values(client):
    register_user(client, "metrics1@example.com", "Password123", "Metrics One")
    token = login_user(client, "metrics1@example.com", "Password123")

    resources = create_base_resources(client, token)

    trade1 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    trade2 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    create_trade(client, token, resources["strategy_id"], resources["broker_id"])

    close_trade(client, token, trade1["id"], pnl=50.25, exit_price=1.1100)
    close_trade(client, token, trade2["id"], pnl=-20.10, exit_price=1.0950)

    response = client.get(
        "/metrics/summary",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["total_trades"] == 3
    assert data["open_trades"] == 1
    assert data["closed_trades"] == 2
    assert data["winning_trades"] == 1
    assert data["losing_trades"] == 1
    assert data["total_pnl"] == "30.15"
    assert data["average_pnl"] == "15.08"
    assert data["win_rate"] == "50.00"


def test_metrics_summary_can_filter_by_strategy(client):
    register_user(client, "metrics2@example.com", "Password123", "Metrics Two")
    token = login_user(client, "metrics2@example.com", "Password123")

    a = create_base_resources(client, token, symbol="EURUSD")
    b = create_base_resources(client, token, symbol="GBPUSD")

    trade_a1 = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    trade_a2 = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    trade_b1 = create_trade(client, token, b["strategy_id"], b["broker_id"], symbol="GBPUSD")

    close_trade(client, token, trade_a1["id"], pnl=10.00)
    close_trade(client, token, trade_a2["id"], pnl=-5.00)
    close_trade(client, token, trade_b1["id"], pnl=99.00)

    response = client.get(
        f"/metrics/summary?strategy_id={a['strategy_id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["total_trades"] == 2
    assert data["open_trades"] == 0
    assert data["closed_trades"] == 2
    assert data["winning_trades"] == 1
    assert data["losing_trades"] == 1
    assert data["total_pnl"] == "5.00"
    assert data["average_pnl"] == "2.50"
    assert data["win_rate"] == "50.00"


def test_metrics_summary_forbids_other_user_strategy(client):
    register_user(client, "metrics-owner@example.com", "Password123", "Metrics Owner")
    owner_token = login_user(client, "metrics-owner@example.com", "Password123")
    owner_resources = create_base_resources(client, owner_token)

    register_user(client, "metrics-attacker@example.com", "Password123", "Metrics Attacker")
    attacker_token = login_user(client, "metrics-attacker@example.com", "Password123")

    response = client.get(
        f"/metrics/summary?strategy_id={owner_resources['strategy_id']}",
        headers=auth_headers(attacker_token),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_metrics_summary_returns_404_for_missing_strategy(client):
    register_user(client, "metrics3@example.com", "Password123", "Metrics Three")
    token = login_user(client, "metrics3@example.com", "Password123")

    response = client.get(
        "/metrics/summary?strategy_id=9999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert "Strategy not found" in response.text
