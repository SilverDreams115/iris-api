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


def create_base_resources(client, token, symbol="EURUSD", label_suffix="ADV"):
    portfolio = client.post(
        "/portfolios/",
        json={
            "name": f"Portfolio Advanced {label_suffix}",
            "description": "portfolio advanced metrics test",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": f"Cuenta Advanced {label_suffix}",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": f"Strategy Advanced {label_suffix}",
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
    response = client.post(
        f"/trades/{trade_id}/close",
        json={
            "exit_price": exit_price,
            "pnl": pnl,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_metrics_summary_returns_advanced_analytics(client):
    register_user(client, "advanced1@example.com", "Password123", "Advanced One")
    token = login_user(client, "advanced1@example.com", "Password123")
    resources = create_base_resources(client, token)

    t1 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    t2 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    t3 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    t4 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])

    close_trade(client, token, t1["id"], pnl=100.00)
    close_trade(client, token, t2["id"], pnl=-40.00)
    close_trade(client, token, t3["id"], pnl=60.00)
    close_trade(client, token, t4["id"], pnl=-20.00)

    response = client.get(
        "/metrics/summary",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["average_win"] == "80.00"
    assert data["average_loss"] == "-30.00"
    assert data["profit_factor"] == "2.67"
    assert data["expectancy"] == "25.00"
    assert data["max_drawdown"] == "40.00"


def test_metrics_summary_handles_all_wins_profit_factor(client):
    register_user(client, "advanced2@example.com", "Password123", "Advanced Two")
    token = login_user(client, "advanced2@example.com", "Password123")
    resources = create_base_resources(client, token, label_suffix="ALLWINS")

    t1 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])
    t2 = create_trade(client, token, resources["strategy_id"], resources["broker_id"])

    close_trade(client, token, t1["id"], pnl=15.00)
    close_trade(client, token, t2["id"], pnl=10.00)

    response = client.get(
        "/metrics/summary",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["average_win"] == "12.50"
    assert data["average_loss"] == "0.00"
    assert data["profit_factor"] == "999999.99"
    assert data["expectancy"] == "12.50"
    assert data["max_drawdown"] == "0.00"


def test_metrics_summary_handles_no_closed_trades_advanced_fields(client):
    register_user(client, "advanced3@example.com", "Password123", "Advanced Three")
    token = login_user(client, "advanced3@example.com", "Password123")
    resources = create_base_resources(client, token, label_suffix="NOCLOSE")

    create_trade(client, token, resources["strategy_id"], resources["broker_id"])

    response = client.get(
        "/metrics/summary",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["average_win"] == "0.00"
    assert data["average_loss"] == "0.00"
    assert data["profit_factor"] == "0.00"
    assert data["expectancy"] == "0.00"
    assert data["max_drawdown"] == "0.00"
