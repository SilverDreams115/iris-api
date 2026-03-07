from app.core.error_messages import (
    NOT_ENOUGH_PERMISSIONS,
    TRADE_STRATEGY_MISMATCH,
    TRADE_STRATEGY_OWNER_MISMATCH,
)
from app.core.exceptions import bad_request, forbidden, not_found


def ensure_exists(resource, detail: str):
    if not resource:
        raise not_found(detail)
    return resource


def ensure_owner_or_admin(current_user, owner_id: int, detail: str = NOT_ENOUGH_PERMISSIONS):
    if current_user.role != "admin" and current_user.id != owner_id:
        raise forbidden(detail)


def ensure_owned_by_current_user(current_user, owner_id: int, detail: str):
    if current_user.role != "admin" and current_user.id != owner_id:
        raise forbidden(detail)


def resolve_owner_scope(current_user):
    return None if current_user.role == "admin" else current_user.id


def ensure_access_to_resource(current_user, resource, detail: str = NOT_ENOUGH_PERMISSIONS):
    ensure_owner_or_admin(current_user, resource.owner_id, detail)
    return resource


def ensure_same_owner(owner_id_a: int, owner_id_b: int, detail: str):
    if owner_id_a != owner_id_b:
        raise bad_request(detail)


def ensure_trade_matches_strategy(trade, strategy):
    ensure_same_owner(
        trade.owner_id,
        strategy.owner_id,
        TRADE_STRATEGY_OWNER_MISMATCH,
    )

    if trade.strategy_id != strategy.id:
        raise bad_request(TRADE_STRATEGY_MISMATCH)
