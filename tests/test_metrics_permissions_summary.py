from conftest import TestingSessionLocal, auth_headers, login_user, register_user

from app.models.user import User


def set_user_role(email: str, role: str) -> None:
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.role = role
        db.commit()
    finally:
        db.close()


def create_portfolio(
    client, token, name="Metrics Portfolio", description="Metrics desc"
):
    response = client.post(
        "/portfolios/",
        json={"name": name, "description": description},
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_broker_account(
    client,
    token,
    broker_name="Metrics Broker",
    account_label="Primary",
    account_type="demo",
):
    response = client.post(
        "/broker-accounts/",
        json={
            "broker_name": broker_name,
            "account_label": account_label,
            "account_type": account_type,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_strategy(client, token, portfolio_id, broker_id, name="Metrics Strategy"):
    response = client.post(
        "/strategies/",
        json={
            "name": name,
            "symbol": "EURUSD",
            "timeframe": "H1",
            "risk_percent": "1.5",
            "portfolio_id": portfolio_id,
            "broker_account_id": broker_id,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_trade(
    client,
    token,
    strategy_id,
    broker_id,
    symbol="EURUSD",
    side="buy",
    volume="0.10",
    entry_price="1.1000",
):
    response = client.post(
        "/trades/",
        json={
            "strategy_id": strategy_id,
            "broker_account_id": broker_id,
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "entry_price": entry_price,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def close_trade(
    client,
    token,
    trade_id: int,
    pnl: str = "25.50",
    exit_price: str = "1.1050",
    closed_at: str = "2024-01-15T12:00:00",
):
    response = client.post(
        f"/trades/{trade_id}/close",
        json={
            "pnl": pnl,
            "exit_price": exit_price,
            "closed_at": closed_at,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_metrics_overview_for_regular_user(client):
    register_user(client, "metrics_user@example.com", "Password123", "Metrics User")
    token = login_user(client, "metrics_user@example.com", "Password123")

    response = client.get("/metrics/overview", headers=auth_headers(token))
    assert response.status_code == 200, response.text

    data = response.json()
    assert "total_trades" in data
    assert "total_pnl" in data


def test_metrics_overview_for_admin(client):
    register_user(client, "metrics_admin@example.com", "Password123", "Metrics Admin")
    set_user_role("metrics_admin@example.com", "admin")
    token = login_user(client, "metrics_admin@example.com", "Password123")

    response = client.get("/metrics/overview", headers=auth_headers(token))
    assert response.status_code == 200, response.text

    data = response.json()
    assert "total_trades" in data
    assert "win_rate" in data


def test_metrics_summary_with_filters(client):
    register_user(client, "metrics_owner@example.com", "Password123", "Metrics Owner")
    token = login_user(client, "metrics_owner@example.com", "Password123")

    portfolio = create_portfolio(client, token, name="Metrics Portfolio")
    broker = create_broker_account(client, token, broker_name="Metrics Broker")
    strategy = create_strategy(client, token, portfolio["id"], broker["id"])

    trade = create_trade(client, token, strategy["id"], broker["id"])
    close_trade(
        client,
        token,
        trade["id"],
        pnl="45.25",
        closed_at="2024-01-15T12:00:00",
    )

    response = client.get(
        (
            f"/metrics/summary?strategy_id={strategy['id']}"
            f"&broker_account_id={broker['id']}"
            f"&portfolio_id={portfolio['id']}"
            f"&symbol=EURUSD"
        ),
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "closed_trades" in data
    assert data["total_trades"] >= 1


def test_metrics_summary_strategy_not_found(client):
    register_user(
        client, "metrics_nf_strategy@example.com", "Password123", "Metrics NF"
    )
    token = login_user(client, "metrics_nf_strategy@example.com", "Password123")

    response = client.get(
        "/metrics/summary?strategy_id=999999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Strategy not found"


def test_metrics_summary_broker_not_found(client):
    register_user(client, "metrics_nf_broker@example.com", "Password123", "Metrics NF")
    token = login_user(client, "metrics_nf_broker@example.com", "Password123")

    response = client.get(
        "/metrics/summary?broker_account_id=999999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Broker account not found"


def test_metrics_summary_portfolio_not_found(client):
    register_user(
        client, "metrics_nf_portfolio@example.com", "Password123", "Metrics NF"
    )
    token = login_user(client, "metrics_nf_portfolio@example.com", "Password123")

    response = client.get(
        "/metrics/summary?portfolio_id=999999",
        headers=auth_headers(token),
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Portfolio not found"


def test_metrics_summary_forbidden_for_foreign_strategy(client):
    register_user(
        client, "metrics_owner_a@example.com", "Password123", "Metrics Owner A"
    )
    token_a = login_user(client, "metrics_owner_a@example.com", "Password123")
    portfolio = create_portfolio(client, token_a, name="Foreign Portfolio")
    broker = create_broker_account(client, token_a, broker_name="Foreign Broker")
    strategy = create_strategy(client, token_a, portfolio["id"], broker["id"])

    register_user(
        client, "metrics_owner_b@example.com", "Password123", "Metrics Owner B"
    )
    token_b = login_user(client, "metrics_owner_b@example.com", "Password123")

    response = client.get(
        f"/metrics/summary?strategy_id={strategy['id']}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not enough permissions"


def test_metrics_by_strategy_forbidden_for_foreign_owner(client):
    register_user(
        client, "metrics_strategy_a@example.com", "Password123", "Metrics Strategy A"
    )
    token_a = login_user(client, "metrics_strategy_a@example.com", "Password123")
    portfolio = create_portfolio(client, token_a, name="Strategy Portfolio")
    broker = create_broker_account(client, token_a, broker_name="Strategy Broker")
    strategy = create_strategy(client, token_a, portfolio["id"], broker["id"])

    register_user(
        client, "metrics_strategy_b@example.com", "Password123", "Metrics Strategy B"
    )
    token_b = login_user(client, "metrics_strategy_b@example.com", "Password123")

    response = client.get(
        f"/metrics/strategies/{strategy['id']}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not enough permissions"


def test_metrics_by_broker_forbidden_for_foreign_owner(client):
    register_user(
        client, "metrics_broker_a@example.com", "Password123", "Metrics Broker A"
    )
    token_a = login_user(client, "metrics_broker_a@example.com", "Password123")
    broker = create_broker_account(client, token_a, broker_name="Restricted Broker")

    register_user(
        client, "metrics_broker_b@example.com", "Password123", "Metrics Broker B"
    )
    token_b = login_user(client, "metrics_broker_b@example.com", "Password123")

    response = client.get(
        f"/metrics/broker-accounts/{broker['id']}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not enough permissions"


def test_metrics_by_portfolio_forbidden_for_foreign_owner(client):
    register_user(
        client, "metrics_portfolio_a@example.com", "Password123", "Metrics Portfolio A"
    )
    token_a = login_user(client, "metrics_portfolio_a@example.com", "Password123")
    portfolio = create_portfolio(client, token_a, name="Restricted Portfolio")

    register_user(
        client, "metrics_portfolio_b@example.com", "Password123", "Metrics Portfolio B"
    )
    token_b = login_user(client, "metrics_portfolio_b@example.com", "Password123")

    response = client.get(
        f"/metrics/portfolios/{portfolio['id']}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not enough permissions"


def test_admin_can_access_foreign_metrics_resources(client):
    register_user(
        client, "metrics_foreign_owner@example.com", "Password123", "Foreign Owner"
    )
    owner_token = login_user(client, "metrics_foreign_owner@example.com", "Password123")
    portfolio = create_portfolio(client, owner_token, name="Admin Visible Portfolio")
    broker = create_broker_account(
        client, owner_token, broker_name="Admin Visible Broker"
    )
    strategy = create_strategy(client, owner_token, portfolio["id"], broker["id"])

    register_user(
        client, "metrics_super_admin@example.com", "Password123", "Metrics Super Admin"
    )
    set_user_role("metrics_super_admin@example.com", "admin")
    admin_token = login_user(client, "metrics_super_admin@example.com", "Password123")

    response_strategy = client.get(
        f"/metrics/strategies/{strategy['id']}",
        headers=auth_headers(admin_token),
    )
    assert response_strategy.status_code == 200, response_strategy.text

    response_broker = client.get(
        f"/metrics/broker-accounts/{broker['id']}",
        headers=auth_headers(admin_token),
    )
    assert response_broker.status_code == 200, response_broker.text

    response_portfolio = client.get(
        f"/metrics/portfolios/{portfolio['id']}",
        headers=auth_headers(admin_token),
    )
    assert response_portfolio.status_code == 200, response_portfolio.text
