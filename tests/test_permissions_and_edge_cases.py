def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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


def create_base_resources(client, token, symbol="EURUSD"):
    portfolio = client.post(
        "/portfolios/",
        json={
            "name": "Test Portfolio",
            "description": "Portfolio for permission tests",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Main Demo",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Permission Strategy",
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

    trade = client.post(
        "/trades/",
        json={
            "symbol": symbol,
            "side": "buy",
            "volume": 0.10,
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "strategy_id": strategy_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert trade.status_code == 201, trade.text
    trade_id = trade.json()["id"]

    signal = client.post(
        "/signals/",
        json={
            "symbol": symbol,
            "side": "buy",
            "confidence": 80,
            "status": "pending",
            "source": "manual",
            "notes": "permission test signal",
            "strategy_id": strategy_id,
        },
        headers=auth_headers(token),
    )
    assert signal.status_code == 201, signal.text
    signal_id = signal.json()["id"]

    return {
        "portfolio_id": portfolio_id,
        "broker_id": broker_id,
        "strategy_id": strategy_id,
        "trade_id": trade_id,
        "signal_id": signal_id,
    }


def test_other_user_cannot_read_trade(client):
    register_user(client, "owner_trade@example.com", "Password123", "Owner Trade")
    owner_token = login_user(client, "owner_trade@example.com", "Password123")
    resources = create_base_resources(client, owner_token)

    register_user(client, "intruder_trade@example.com", "Password123", "Intruder Trade")
    intruder_token = login_user(client, "intruder_trade@example.com", "Password123")

    response = client.get(
        f"/trades/{resources['trade_id']}",
        headers=auth_headers(intruder_token),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_other_user_cannot_update_signal(client):
    register_user(client, "owner_signal@example.com", "Password123", "Owner Signal")
    owner_token = login_user(client, "owner_signal@example.com", "Password123")
    resources = create_base_resources(client, owner_token)

    register_user(client, "intruder_signal@example.com", "Password123", "Intruder Signal")
    intruder_token = login_user(client, "intruder_signal@example.com", "Password123")

    response = client.patch(
        f"/signals/{resources['signal_id']}",
        json={"notes": "hacked note"},
        headers=auth_headers(intruder_token),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_cannot_close_trade_twice(client):
    register_user(client, "closer@example.com", "Password123", "Closer")
    token = login_user(client, "closer@example.com", "Password123")
    resources = create_base_resources(client, token)

    first = client.post(
        f"/trades/{resources['trade_id']}/close",
        json={
            "exit_price": 1.1080,
            "pnl": 25.5,
        },
        headers=auth_headers(token),
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/trades/{resources['trade_id']}/close",
        json={
            "exit_price": 1.1090,
            "pnl": 30.0,
        },
        headers=auth_headers(token),
    )
    assert second.status_code == 409, second.text
    assert "Only open trades can be closed" in second.text


def test_cannot_read_nonexistent_signal(client):
    register_user(client, "reader@example.com", "Password123", "Reader")
    token = login_user(client, "reader@example.com", "Password123")

    response = client.get(
        "/signals/999999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert "Signal not found" in response.text


def test_other_user_cannot_delete_strategy(client):
    register_user(client, "owner_strategy@example.com", "Password123", "Owner Strategy")
    owner_token = login_user(client, "owner_strategy@example.com", "Password123")
    resources = create_base_resources(client, owner_token)

    register_user(client, "intruder_strategy@example.com", "Password123", "Intruder Strategy")
    intruder_token = login_user(client, "intruder_strategy@example.com", "Password123")

    response = client.delete(
        f"/strategies/{resources['strategy_id']}",
        headers=auth_headers(intruder_token),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_other_user_cannot_read_user_profile(client):
    register_user(client, "user_a@example.com", "Password123", "User A")
    token_a = login_user(client, "user_a@example.com", "Password123")

    register_user(client, "user_b@example.com", "Password123", "User B")
    token_b = login_user(client, "user_b@example.com", "Password123")

    me_a = client.get("/auth/me", headers=auth_headers(token_a))
    assert me_a.status_code == 200, me_a.text
    user_a_id = me_a.json()["id"]

    response = client.get(
        f"/users/{user_a_id}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text
