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


def create_base_resources(client, token, symbol="EURUSD", label_suffix="A"):
    portfolio = client.post(
        "/portfolios/",
        json={
            "name": f"Portfolio Filters {label_suffix}",
            "description": "portfolio filters test",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": f"Cuenta Filters {label_suffix}",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": f"Strategy {symbol} {label_suffix}",
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


def test_metrics_summary_can_filter_by_symbol(client):
    register_user(client, "filters1@example.com", "Password123", "Filters One")
    token = login_user(client, "filters1@example.com", "Password123")

    a = create_base_resources(client, token, symbol="EURUSD", label_suffix="A")
    b = create_base_resources(client, token, symbol="GBPUSD", label_suffix="B")

    trade_a1 = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    trade_a2 = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    trade_b1 = create_trade(client, token, b["strategy_id"], b["broker_id"], symbol="GBPUSD")

    close_trade(client, token, trade_a1["id"], pnl=12.50)
    close_trade(client, token, trade_a2["id"], pnl=-2.50)
    close_trade(client, token, trade_b1["id"], pnl=99.00)

    response = client.get(
        "/metrics/summary?symbol=EURUSD",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["total_trades"] == 2
    assert data["closed_trades"] == 2
    assert data["total_pnl"] == "10.00"
    assert data["average_pnl"] == "5.00"
    assert data["win_rate"] == "50.00"


def test_metrics_summary_can_filter_by_broker_account_and_portfolio(client):
    register_user(client, "filters2@example.com", "Password123", "Filters Two")
    token = login_user(client, "filters2@example.com", "Password123")

    a = create_base_resources(client, token, symbol="EURUSD", label_suffix="A")
    b = create_base_resources(client, token, symbol="USDJPY", label_suffix="B")

    trade_a = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    trade_b = create_trade(client, token, b["strategy_id"], b["broker_id"], symbol="USDJPY")

    close_trade(client, token, trade_a["id"], pnl=7.00)
    close_trade(client, token, trade_b["id"], pnl=13.00)

    response_broker = client.get(
        f"/metrics/summary?broker_account_id={a['broker_id']}",
        headers=auth_headers(token),
    )
    assert response_broker.status_code == 200, response_broker.text
    broker_data = response_broker.json()
    assert broker_data["total_trades"] == 1
    assert broker_data["total_pnl"] == "7.00"

    response_portfolio = client.get(
        f"/metrics/summary?portfolio_id={b['portfolio_id']}",
        headers=auth_headers(token),
    )
    assert response_portfolio.status_code == 200, response_portfolio.text
    portfolio_data = response_portfolio.json()
    assert portfolio_data["total_trades"] == 1
    assert portfolio_data["total_pnl"] == "13.00"


def test_metrics_summary_can_filter_by_closed_date_range(client):
    register_user(client, "filters3@example.com", "Password123", "Filters Three")
    token = login_user(client, "filters3@example.com", "Password123")

    a = create_base_resources(client, token, symbol="EURUSD", label_suffix="A")
    trade = create_trade(client, token, a["strategy_id"], a["broker_id"], symbol="EURUSD")
    close_trade(client, token, trade["id"], pnl=11.00)

    in_range = client.get(
        "/metrics/summary?closed_from=2000-01-01T00:00:00Z&closed_to=2999-01-01T00:00:00Z",
        headers=auth_headers(token),
    )
    assert in_range.status_code == 200, in_range.text
    in_range_data = in_range.json()
    assert in_range_data["total_trades"] == 1
    assert in_range_data["closed_trades"] == 1
    assert in_range_data["total_pnl"] == "11.00"

    out_of_range = client.get(
        "/metrics/summary?closed_from=2999-01-02T00:00:00Z&closed_to=2999-12-31T00:00:00Z",
        headers=auth_headers(token),
    )
    assert out_of_range.status_code == 200, out_of_range.text
    out_of_range_data = out_of_range.json()
    assert out_of_range_data["total_trades"] == 0
    assert out_of_range_data["closed_trades"] == 0
    assert out_of_range_data["total_pnl"] == "0.00"


def test_metrics_summary_returns_404_for_missing_broker_account(client):
    register_user(client, "filters4@example.com", "Password123", "Filters Four")
    token = login_user(client, "filters4@example.com", "Password123")

    response = client.get(
        "/metrics/summary?broker_account_id=9999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert "Broker account not found" in response.text


def test_metrics_summary_returns_404_for_missing_portfolio(client):
    register_user(client, "filters5@example.com", "Password123", "Filters Five")
    token = login_user(client, "filters5@example.com", "Password123")

    response = client.get(
        "/metrics/summary?portfolio_id=9999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert "Portfolio not found" in response.text
