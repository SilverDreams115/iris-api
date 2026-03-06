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
            "name": "Portfolio Test",
            "description": "portfolio de prueba",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Cuenta Demo",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Test",
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

    signal = client.post(
        "/signals/",
        json={
            "symbol": symbol,
            "side": "buy",
            "confidence": 85,
            "status": "pending",
            "source": "manual",
            "notes": "signal de prueba",
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
        "signal_id": signal_id,
    }


def execute_signal(client, token, signal_id):
    return client.post(
        f"/signals/{signal_id}/execute",
        json={
            "volume": 0.10,
            "entry_price": 1.0845,
            "stop_loss": 1.0800,
            "take_profit": 1.0900,
        },
        headers=auth_headers(token),
    )


def test_execute_signal_creates_trade_and_updates_signal(client):
    register_user(client, "user1@example.com", "Password123", "User One")
    token = login_user(client, "user1@example.com", "Password123")

    resources = create_base_resources(client, token)

    response = execute_signal(client, token, resources["signal_id"])
    assert response.status_code == 201, response.text

    trade = response.json()
    assert trade["symbol"] == "EURUSD"
    assert trade["side"] == "buy"
    assert trade["status"] == "open"
    assert trade["strategy_id"] == resources["strategy_id"]
    assert trade["broker_account_id"] == resources["broker_id"]

    signal_response = client.get(
        f"/signals/{resources['signal_id']}",
        headers=auth_headers(token),
    )
    assert signal_response.status_code == 200, signal_response.text

    signal_data = signal_response.json()
    assert signal_data["status"] == "executed"
    assert signal_data["trade_id"] == trade["id"]


def test_cannot_execute_signal_twice(client):
    register_user(client, "user2@example.com", "Password123", "User Two")
    token = login_user(client, "user2@example.com", "Password123")

    resources = create_base_resources(client, token)

    first = execute_signal(client, token, resources["signal_id"])
    assert first.status_code == 201, first.text

    second = execute_signal(client, token, resources["signal_id"])
    assert second.status_code == 409, second.text
    assert "Only pending or triggered signals can be executed" in second.text


def test_cannot_execute_signal_from_other_user(client):
    register_user(client, "owner@example.com", "Password123", "Owner User")
    owner_token = login_user(client, "owner@example.com", "Password123")
    resources = create_base_resources(client, owner_token)

    register_user(client, "attacker@example.com", "Password123", "Attacker User")
    attacker_token = login_user(client, "attacker@example.com", "Password123")

    response = execute_signal(client, attacker_token, resources["signal_id"])
    assert response.status_code == 403, response.text
    assert "Not enough permissions" in response.text


def test_cannot_execute_signal_if_strategy_is_inactive(client):
    register_user(client, "user3@example.com", "Password123", "User Three")
    token = login_user(client, "user3@example.com", "Password123")
    resources = create_base_resources(client, token)

    patch_strategy = client.patch(
        f"/strategies/{resources['strategy_id']}",
        json={"is_active": False},
        headers=auth_headers(token),
    )
    assert patch_strategy.status_code == 200, patch_strategy.text

    response = execute_signal(client, token, resources["signal_id"])
    assert response.status_code == 409, response.text
    assert "Strategy is inactive" in response.text


def test_cannot_execute_signal_if_broker_account_is_inactive(client):
    register_user(client, "user4@example.com", "Password123", "User Four")
    token = login_user(client, "user4@example.com", "Password123")
    resources = create_base_resources(client, token)

    patch_broker = client.patch(
        f"/broker-accounts/{resources['broker_id']}",
        json={"status": "inactive"},
        headers=auth_headers(token),
    )
    assert patch_broker.status_code == 200, patch_broker.text

    response = execute_signal(client, token, resources["signal_id"])
    assert response.status_code == 409, response.text
    assert "Broker account is not active" in response.text


def test_cannot_execute_buy_signal_with_invalid_price_relationship(client):
    register_user(client, "user5@example.com", "Password123", "User Five")
    token = login_user(client, "user5@example.com", "Password123")

    resources = create_base_resources(client, token, symbol="EURUSD")

    response = client.post(
        f"/signals/{resources['signal_id']}/execute",
        json={
            "volume": 0.10,
            "entry_price": 1.0845,
            "stop_loss": 1.0900,
            "take_profit": 1.0800,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 409, response.text
    assert "Invalid price relationship for buy signal" in response.text


def test_cannot_execute_sell_signal_with_invalid_price_relationship(client):
    register_user(client, "user6@example.com", "Password123", "User Six")
    token = login_user(client, "user6@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={
            "name": "Portfolio Sell Test",
            "description": "portfolio de prueba sell",
        },
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Cuenta Demo Sell",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Sell Test",
            "symbol": "GBPUSD",
            "timeframe": "H1",
            "risk_percent": 1.5,
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text
    strategy_id = strategy.json()["id"]

    signal = client.post(
        "/signals/",
        json={
            "symbol": "GBPUSD",
            "side": "sell",
            "confidence": 80,
            "status": "pending",
            "source": "manual",
            "notes": "signal sell de prueba",
            "strategy_id": strategy_id,
        },
        headers=auth_headers(token),
    )
    assert signal.status_code == 201, signal.text
    signal_id = signal.json()["id"]

    response = client.post(
        f"/signals/{signal_id}/execute",
        json={
            "volume": 0.10,
            "entry_price": 1.2500,
            "stop_loss": 1.2400,
            "take_profit": 1.2600,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 409, response.text
    assert "Invalid price relationship for sell signal" in response.text


def test_execute_signal_sets_executed_at(client):
    register_user(client, "user7@example.com", "Password123", "User Seven")
    token = login_user(client, "user7@example.com", "Password123")

    resources = create_base_resources(client, token)

    response = execute_signal(client, token, resources["signal_id"])
    assert response.status_code == 201, response.text

    signal_response = client.get(
        f"/signals/{resources['signal_id']}",
        headers=auth_headers(token),
    )
    assert signal_response.status_code == 200, signal_response.text

    signal_data = signal_response.json()
    assert signal_data["status"] == "executed"
    assert signal_data["executed_at"] is not None
    assert signal_data["rejection_reason"] is None


def test_cannot_execute_cancelled_signal(client):
    register_user(client, "user8@example.com", "Password123", "User Eight")
    token = login_user(client, "user8@example.com", "Password123")

    resources = create_base_resources(client, token)

    patch_signal = client.patch(
        f"/signals/{resources['signal_id']}",
        json={
            "status": "cancelled",
            "rejection_reason": "cancelled manually before execution",
        },
        headers=auth_headers(token),
    )
    assert patch_signal.status_code == 200, patch_signal.text

    response = execute_signal(client, token, resources["signal_id"])
    assert response.status_code == 409, response.text
    assert "Only pending or triggered signals can be executed" in response.text

    signal_response = client.get(
        f"/signals/{resources['signal_id']}",
        headers=auth_headers(token),
    )
    assert signal_response.status_code == 200, signal_response.text

    signal_data = signal_response.json()
    assert signal_data["status"] == "cancelled"
    assert signal_data["rejection_reason"] == "cancelled manually before execution"
