from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional


try:
    from prices import get_share_price  # type: ignore
except Exception:  # pragma: no cover
    def get_share_price(symbol: str) -> float:
        raise KeyError(symbol)


SUPPORTED_TRANSACTION_TYPES = {"deposit", "withdraw", "buy", "sell"}


@dataclass(frozen=True)
class Transaction:
    timestamp: str
    type: str
    symbol: Optional[str]
    quantity: Optional[int]
    amount: Optional[float]
    price: Optional[float]
    cash_balance_after: float
    note: Optional[str] = None


@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: int


class AccountManager:
    def __init__(self, price_provider: Callable[[str], float] = get_share_price) -> None:
        self.price_provider = price_provider
        self.create_account()

    def create_account(self) -> None:
        self.cash_balance = 0.0
        self.initial_deposits_total = 0.0
        self.holdings: dict[str, int] = {}
        self.transactions: list[Transaction] = []

    def _format_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _validate_positive_amount(self, amount: float, field_name: str) -> None:
        if amount is None or amount <= 0:
            raise ValueError(f"{field_name} must be positive")

    def _validate_positive_quantity(self, quantity: int, field_name: str) -> None:
        if quantity is None or quantity <= 0:
            raise ValueError(f"{field_name} must be positive")

    def _validate_symbol(self, symbol: str) -> str:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("Symbol must be a non-empty string")
        return symbol.strip().upper()

    def _get_price(self, symbol: str) -> float:
        try:
            price = float(self.price_provider(symbol))
        except KeyError as exc:
            raise ValueError(f"Unknown symbol: {symbol}") from exc
        except Exception as exc:
            raise ValueError(f"Unknown symbol: {symbol}") from exc
        if price <= 0:
            raise ValueError(f"Invalid price for symbol: {symbol}")
        return price

    def _record_transaction(
        self,
        type_: str,
        *,
        symbol: Optional[str] = None,
        quantity: Optional[int] = None,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        note: Optional[str] = None,
    ) -> Transaction:
        txn = Transaction(
            timestamp=self._format_timestamp(),
            type=type_,
            symbol=symbol,
            quantity=quantity,
            amount=amount,
            price=price,
            cash_balance_after=self.cash_balance,
            note=note,
        )
        self.transactions.append(txn)
        return txn

    def deposit(self, amount: float) -> Transaction:
        self._validate_positive_amount(amount, "Deposit amount")
        self.cash_balance += float(amount)
        self.initial_deposits_total += float(amount)
        return self._record_transaction("deposit", amount=float(amount))

    def withdraw(self, amount: float) -> Transaction:
        self._validate_positive_amount(amount, "Withdrawal amount")
        if amount > self.cash_balance:
            raise ValueError("Insufficient cash balance for withdrawal")
        self.cash_balance -= float(amount)
        return self._record_transaction("withdraw", amount=float(amount))

    def buy_shares(self, symbol: str, quantity: int) -> Transaction:
        symbol = self._validate_symbol(symbol)
        self._validate_positive_quantity(quantity, "Buy quantity")
        price = self._get_price(symbol)
        total_cost = price * quantity
        if total_cost > self.cash_balance:
            raise ValueError("Insufficient cash balance for purchase")
        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        return self._record_transaction(
            "buy", symbol=symbol, quantity=quantity, amount=total_cost, price=price
        )

    def sell_shares(self, symbol: str, quantity: int) -> Transaction:
        symbol = self._validate_symbol(symbol)
        self._validate_positive_quantity(quantity, "Sell quantity")
        current_qty = self.holdings.get(symbol, 0)
        if quantity > current_qty:
            raise ValueError(f"Insufficient shares of {symbol} to sell")
        price = self._get_price(symbol)
        proceeds = price * quantity
        self.cash_balance += proceeds
        remaining = current_qty - quantity
        if remaining:
            self.holdings[symbol] = remaining
        else:
            self.holdings.pop(symbol, None)
        return self._record_transaction(
            "sell", symbol=symbol, quantity=quantity, amount=proceeds, price=price
        )

    def get_holdings(self) -> dict[str, int]:
        return dict(self.holdings)

    def get_transactions(self) -> list[Transaction]:
        return list(self.transactions)

    def get_portfolio_value(self) -> float:
        value = self.cash_balance
        for symbol, quantity in self.holdings.items():
            value += self._get_price(symbol) * quantity
        return value

    def get_profit_loss(self) -> float:
        return self.get_portfolio_value() - self.initial_deposits_total

    def get_account_summary(self) -> dict[str, object]:
        return {
            "cash_balance": self.cash_balance,
            "initial_deposits_total": self.initial_deposits_total,
            "portfolio_value": self.get_portfolio_value(),
            "profit_loss": self.get_profit_loss(),
            "holdings": self.get_holdings(),
            "transaction_count": len(self.transactions),
        }


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def serialize_transactions(transactions: list[Transaction]) -> list[dict[str, object]]:
    return [txn.__dict__.copy() for txn in transactions]
