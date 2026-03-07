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


def test_owner_cannot_create_duplicate_strategy_name(client):
    register_user(client, "strategy_dup@example.com", "Password123", "Strategy Dup")
    token = login_user(client, "strategy_dup@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Strategy Dup", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text
    portfolio_id = portfolio.json()["id"]

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Strategy Dup",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text
    broker_id = broker.json()["id"]

    response_one = client.post(
        "/strategies/",
        json={
            "name": "Main Strategy",
            "symbol": "eurusd",
            "timeframe": "H1",
            "risk_percent": "2.50",
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert response_one.status_code == 201, response_one.text
    assert response_one.json()["symbol"] == "EURUSD"

    response_two = client.post(
        "/strategies/",
        json={
            "name": "Main Strategy",
            "symbol": "gbpusd",
            "timeframe": "H4",
            "risk_percent": "1.50",
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert response_two.status_code == 409, response_two.text
    assert response_two.json()["detail"] == "Strategy name already exists for this user"


def test_different_users_can_use_same_strategy_name(client):
    register_user(client, "strategy_dup_a@example.com", "Password123", "Strategy Dup A")
    token_a = login_user(client, "strategy_dup_a@example.com", "Password123")

    portfolio_a = client.post(
        "/portfolios/",
        json={"name": "Portfolio A Strategy Same", "description": "desc"},
        headers=auth_headers(token_a),
    )
    assert portfolio_a.status_code == 201, portfolio_a.text

    broker_a = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker A Strategy Same",
            "account_type": "demo",
        },
        headers=auth_headers(token_a),
    )
    assert broker_a.status_code == 201, broker_a.text

    response_a = client.post(
        "/strategies/",
        json={
            "name": "Shared Strategy Name",
            "symbol": "eurusd",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio_a.json()["id"],
            "broker_account_id": broker_a.json()["id"],
        },
        headers=auth_headers(token_a),
    )
    assert response_a.status_code == 201, response_a.text

    register_user(client, "strategy_dup_b@example.com", "Password123", "Strategy Dup B")
    token_b = login_user(client, "strategy_dup_b@example.com", "Password123")

    portfolio_b = client.post(
        "/portfolios/",
        json={"name": "Portfolio B Strategy Same", "description": "desc"},
        headers=auth_headers(token_b),
    )
    assert portfolio_b.status_code == 201, portfolio_b.text

    broker_b = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker B Strategy Same",
            "account_type": "demo",
        },
        headers=auth_headers(token_b),
    )
    assert broker_b.status_code == 201, broker_b.text

    response_b = client.post(
        "/strategies/",
        json={
            "name": "Shared Strategy Name",
            "symbol": "gbpusd",
            "timeframe": "H4",
            "risk_percent": "1.00",
            "portfolio_id": portfolio_b.json()["id"],
            "broker_account_id": broker_b.json()["id"],
        },
        headers=auth_headers(token_b),
    )
    assert response_b.status_code == 201, response_b.text


def test_strategy_name_cannot_be_blank_and_symbol_is_normalized(client):
    register_user(client, "strategy_blank@example.com", "Password123", "Strategy Blank")
    token = login_user(client, "strategy_blank@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Strategy Blank", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Strategy Blank",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    invalid = client.post(
        "/strategies/",
        json={
            "name": "   ",
            "symbol": " eurusd ",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert invalid.status_code == 422, invalid.text

    valid = client.post(
        "/strategies/",
        json={
            "name": "Normalized Strategy",
            "symbol": " eurusd ",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert valid.status_code == 201, valid.text
    assert valid.json()["symbol"] == "EURUSD"


def test_signal_symbol_is_normalized_to_uppercase(client):
    register_user(client, "signal_norm@example.com", "Password123", "Signal Norm")
    token = login_user(client, "signal_norm@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Signal Norm", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Signal Norm",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Signal Norm",
            "symbol": " eurusd ",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    signal = client.post(
        "/signals/",
        json={
            "symbol": " eurusd ",
            "side": "buy",
            "confidence": "75.50",
            "status": "pending",
            "source": "manual",
            "notes": "  signal de prueba  ",
            "strategy_id": strategy.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert signal.status_code == 201, signal.text
    data = signal.json()
    assert data["symbol"] == "EURUSD"
    assert data["notes"] == "signal de prueba"


def test_rejected_signal_requires_non_blank_reason(client):
    register_user(client, "signal_reason@example.com", "Password123", "Signal Reason")
    token = login_user(client, "signal_reason@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Signal Reason", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Signal Reason",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Signal Reason",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    invalid = client.post(
        "/signals/",
        json={
            "symbol": "EURUSD",
            "side": "buy",
            "confidence": "80.00",
            "status": "rejected",
            "source": "manual",
            "rejection_reason": "   ",
            "strategy_id": strategy.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert invalid.status_code == 422, invalid.text


def test_reject_signal_trims_reason(client):
    register_user(client, "signal_reject_trim@example.com", "Password123", "Signal Reject Trim")
    token = login_user(client, "signal_reject_trim@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Signal Reject Trim", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Signal Reject Trim",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Signal Reject Trim",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    signal = client.post(
        "/signals/",
        json={
            "symbol": "EURUSD",
            "side": "buy",
            "confidence": "80.00",
            "status": "pending",
            "source": "manual",
            "strategy_id": strategy.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert signal.status_code == 201, signal.text

    rejected = client.post(
        f"/signals/{signal.json()['id']}/reject",
        json={"rejection_reason": "  invalid setup  "},
        headers=auth_headers(token),
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["rejection_reason"] == "invalid setup"


def test_trade_symbol_is_normalized_to_uppercase(client):
    register_user(client, "trade_norm@example.com", "Password123", "Trade Norm")
    token = login_user(client, "trade_norm@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Trade Norm", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Trade Norm",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Trade Norm",
            "symbol": " eurusd ",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    trade = client.post(
        "/trades/",
        json={
            "symbol": " eurusd ",
            "side": "buy",
            "volume": "1.00",
            "entry_price": "1.1000",
            "stop_loss": "1.0900",
            "take_profit": "1.1200",
            "strategy_id": strategy.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert trade.status_code == 201, trade.text
    assert trade.json()["symbol"] == "EURUSD"


def test_cannot_create_buy_trade_with_invalid_price_relationship(client):
    register_user(client, "trade_buy_invalid@example.com", "Password123", "Trade Buy Invalid")
    token = login_user(client, "trade_buy_invalid@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Buy Invalid", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Buy Invalid",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Buy Invalid",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    trade = client.post(
        "/trades/",
        json={
            "symbol": "EURUSD",
            "side": "buy",
            "volume": "1.00",
            "entry_price": "1.1000",
            "stop_loss": "1.1100",
            "take_profit": "1.0900",
            "strategy_id": strategy.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert trade.status_code == 422, trade.text


def test_cannot_create_sell_trade_with_invalid_price_relationship(client):
    register_user(client, "trade_sell_invalid@example.com", "Password123", "Trade Sell Invalid")
    token = login_user(client, "trade_sell_invalid@example.com", "Password123")

    portfolio = client.post(
        "/portfolios/",
        json={"name": "Portfolio Sell Invalid", "description": "desc"},
        headers=auth_headers(token),
    )
    assert portfolio.status_code == 201, portfolio.text

    broker = client.post(
        "/broker-accounts/",
        json={
            "broker_name": "Demo Broker",
            "account_label": "Broker Sell Invalid",
            "account_type": "demo",
        },
        headers=auth_headers(token),
    )
    assert broker.status_code == 201, broker.text

    strategy = client.post(
        "/strategies/",
        json={
            "name": "Strategy Sell Invalid",
            "symbol": "GBPUSD",
            "timeframe": "H1",
            "risk_percent": "2.00",
            "portfolio_id": portfolio.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert strategy.status_code == 201, strategy.text

    trade = client.post(
        "/trades/",
        json={
            "symbol": "GBPUSD",
            "side": "sell",
            "volume": "1.00",
            "entry_price": "1.2500",
            "stop_loss": "1.2400",
            "take_profit": "1.2600",
            "strategy_id": strategy.json()["id"],
            "broker_account_id": broker.json()["id"],
        },
        headers=auth_headers(token),
    )
    assert trade.status_code == 422, trade.text
