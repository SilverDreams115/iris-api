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


def create_portfolio(client, token, name):
    response = client.post(
        "/portfolios/",
        json={
            "name": name,
            "description": f"{name} description",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_broker_account(client, token, label):
    response = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": label,
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_strategy(
    client, token, portfolio_id, broker_account_id, name="Strategy A", symbol="EURUSD"
):
    response = client.post(
        "/strategies/",
        json={
            "name": name,
            "symbol": symbol,
            "timeframe": "H1",
            "risk_percent": 1.5,
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_account_id,
        },
        headers=auth_headers(token),
    )
    return response


def create_trade(client, token, strategy_id, broker_account_id, symbol="EURUSD"):
    response = client.post(
        "/trades/",
        json={
            "symbol": symbol,
            "side": "buy",
            "volume": 0.10,
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "strategy_id": strategy_id,
            "broker_account_id": broker_account_id,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_signal(client, token, strategy_id, trade_id=None, symbol="EURUSD"):
    payload = {
        "symbol": symbol,
        "side": "buy",
        "confidence": 85,
        "status": "pending",
        "source": "manual",
        "notes": "integrity test",
        "strategy_id": strategy_id,
    }
    if trade_id is not None:
        payload["trade_id"] = trade_id

    response = client.post(
        "/signals/",
        json=payload,
        headers=auth_headers(token),
    )
    return response


def test_cannot_create_strategy_with_portfolio_and_broker_from_different_owners(client):
    register_user(client, "owner_a@example.com", "Password123", "Owner A")
    token_a = login_user(client, "owner_a@example.com", "Password123")

    register_user(client, "owner_b@example.com", "Password123", "Owner B")
    token_b = login_user(client, "owner_b@example.com", "Password123")

    portfolio_id = create_portfolio(client, token_a, "Portfolio A")
    broker_account_id = create_broker_account(client, token_b, "Broker B")

    response = create_strategy(client, token_a, portfolio_id, broker_account_id)
    assert response.status_code == 400, response.text
    assert "Portfolio and broker account must belong to the same owner" in response.text


def test_cannot_update_strategy_with_broker_from_different_owner(client):
    register_user(client, "owner_c@example.com", "Password123", "Owner C")
    token_c = login_user(client, "owner_c@example.com", "Password123")

    register_user(client, "owner_d@example.com", "Password123", "Owner D")
    token_d = login_user(client, "owner_d@example.com", "Password123")

    portfolio_id = create_portfolio(client, token_c, "Portfolio C")
    broker_account_id = create_broker_account(client, token_c, "Broker C")
    foreign_broker_account_id = create_broker_account(client, token_d, "Broker D")

    strategy_response = create_strategy(client, token_c, portfolio_id, broker_account_id)
    assert strategy_response.status_code == 201, strategy_response.text
    strategy_id = strategy_response.json()["id"]

    response = client.patch(
        f"/strategies/{strategy_id}",
        json={
            "broker_account_id": foreign_broker_account_id,
        },
        headers=auth_headers(token_c),
    )
    assert response.status_code == 400, response.text
    assert "Portfolio and broker account must belong to the same owner" in response.text


def test_cannot_create_signal_with_trade_from_different_strategy(client):
    register_user(client, "owner_e@example.com", "Password123", "Owner E")
    token = login_user(client, "owner_e@example.com", "Password123")

    portfolio_id = create_portfolio(client, token, "Portfolio E")
    broker_account_id = create_broker_account(client, token, "Broker E")

    strategy_one = create_strategy(
        client,
        token,
        portfolio_id,
        broker_account_id,
        name="Strategy One",
        symbol="EURUSD",
    )
    assert strategy_one.status_code == 201, strategy_one.text
    strategy_one_id = strategy_one.json()["id"]

    strategy_two = create_strategy(
        client,
        token,
        portfolio_id,
        broker_account_id,
        name="Strategy Two",
        symbol="GBPUSD",
    )
    assert strategy_two.status_code == 201, strategy_two.text
    strategy_two_id = strategy_two.json()["id"]

    trade_id = create_trade(client, token, strategy_one_id, broker_account_id, symbol="EURUSD")

    response = create_signal(
        client,
        token,
        strategy_id=strategy_two_id,
        trade_id=trade_id,
        symbol="GBPUSD",
    )
    assert response.status_code == 400, response.text
    assert "Trade must belong to the provided strategy" in response.text


def test_cannot_update_signal_with_trade_from_different_strategy(client):
    register_user(client, "owner_f@example.com", "Password123", "Owner F")
    token = login_user(client, "owner_f@example.com", "Password123")

    portfolio_id = create_portfolio(client, token, "Portfolio F")
    broker_account_id = create_broker_account(client, token, "Broker F")

    strategy_one = create_strategy(
        client,
        token,
        portfolio_id,
        broker_account_id,
        name="Strategy F1",
        symbol="EURUSD",
    )
    assert strategy_one.status_code == 201, strategy_one.text
    strategy_one_id = strategy_one.json()["id"]

    strategy_two = create_strategy(
        client,
        token,
        portfolio_id,
        broker_account_id,
        name="Strategy F2",
        symbol="GBPUSD",
    )
    assert strategy_two.status_code == 201, strategy_two.text
    strategy_two_id = strategy_two.json()["id"]

    trade_id = create_trade(client, token, strategy_one_id, broker_account_id, symbol="EURUSD")

    signal_response = create_signal(client, token, strategy_id=strategy_two_id, symbol="GBPUSD")
    assert signal_response.status_code == 201, signal_response.text
    signal_id = signal_response.json()["id"]

    response = client.patch(
        f"/signals/{signal_id}",
        json={"trade_id": trade_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 400, response.text
    assert "Trade must belong to the provided strategy" in response.text
