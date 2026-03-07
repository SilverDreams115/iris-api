from decimal import Decimal

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: Decimal
    average_pnl: Decimal
    win_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    profit_factor: Decimal
    expectancy: Decimal
    max_drawdown: Decimal
