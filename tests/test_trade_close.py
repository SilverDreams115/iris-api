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
            "name": "Portfolio Trade Close",
            "description": "portfolio close test",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Cuenta Close",
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


def create_trade(
    client, token, strategy_id, broker_account_id, symbol="EURUSD", side="buy"
):
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


def test_close_trade_sets_status_exit_price_pnl_and_timestamp(client):
    register_user(client, "close1@example.com", "Password123", "Close One")
    token = login_user(client, "close1@example.com", "Password123")
    resources = create_base_resources(client, token)

    trade = create_trade(
        client, token, resources["strategy_id"], resources["broker_id"]
    )

    response = client.post(
        f"/trades/{trade['id']}/close",
        json={
            "exit_price": 1.1100,
            "pnl": 42.55,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "closed"
    assert data["exit_price"] == "1.11000000"
    assert data["pnl"] == "42.55000000"
    assert data["closed_at"] is not None


def test_cannot_close_trade_twice(client):
    register_user(client, "close2@example.com", "Password123", "Close Two")
    token = login_user(client, "close2@example.com", "Password123")
    resources = create_base_resources(client, token)

    trade = create_trade(
        client, token, resources["strategy_id"], resources["broker_id"]
    )

    first = client.post(
        f"/trades/{trade['id']}/close",
        json={
            "exit_price": 1.1100,
            "pnl": 10.00,
        },
        headers=auth_headers(token),
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/trades/{trade['id']}/close",
        json={
            "exit_price": 1.1150,
            "pnl": 12.00,
        },
        headers=auth_headers(token),
    )
    assert second.status_code == 409, second.text
    assert "Only open trades can be closed" in second.text


def test_other_user_cannot_close_trade(client):
    register_user(client, "close-owner@example.com", "Password123", "Close Owner")
    owner_token = login_user(client, "close-owner@example.com", "Password123")
    resources = create_base_resources(client, owner_token)

    trade = create_trade(
        client, owner_token, resources["strategy_id"], resources["broker_id"]
    )

    register_user(client, "close-attacker@example.com", "Password123", "Close Attacker")
    attacker_token = login_user(client, "close-attacker@example.com", "Password123")

    response = client.post(
        f"/trades/{trade['id']}/close",
        json={
            "exit_price": 1.1100,
            "pnl": 8.00,
        },
        headers=auth_headers(attacker_token),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_close_trade_returns_404_for_missing_trade(client):
    register_user(client, "close3@example.com", "Password123", "Close Three")
    token = login_user(client, "close3@example.com", "Password123")

    response = client.post(
        "/trades/9999/close",
        json={
            "exit_price": 1.1100,
            "pnl": 5.00,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert "Trade not found" in response.text
