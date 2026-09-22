```python
# test_backend.py
import unittest

from backend import AccountManager


def fake_price_provider(symbol: str) -> float:
    prices = {"AAPL": 100.0, "TSLA": 200.0, "GOOGL": 150.0}
    if symbol not in prices:
        raise KeyError(symbol)
    return prices[symbol]


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.account = AccountManager(price_provider=fake_price_provider)

    def test_create_account_initial_state(self):
        self.account.create_account()
        self.assertEqual(self.account.cash_balance, 0.0)
        self.assertEqual(self.account.initial_deposits_total, 0.0)
        self.assertEqual(self.account.get_holdings(), {})
        self.assertEqual(self.account.get_transactions(), [])

    def test_deposit_updates_balance_and_initial_deposit(self):
        txn = self.account.deposit(500.0)
        self.assertEqual(self.account.cash_balance, 500.0)
        self.assertEqual(self.account.initial_deposits_total, 500.0)
        self.assertEqual(txn.type, "deposit")
        self.assertEqual(len(self.account.get_transactions()), 1)

    def test_withdraw_updates_balance(self):
        self.account.deposit(500.0)
        txn = self.account.withdraw(200.0)
        self.assertEqual(self.account.cash_balance, 300.0)
        self.assertEqual(txn.type, "withdraw")

    def test_withdraw_cannot_overdraw(self):
        self.account.deposit(100.0)
        with self.assertRaises(ValueError):
            self.account.withdraw(150.0)

    def test_buy_shares_updates_holdings_and_cash(self):
        self.account.deposit(1000.0)
        txn = self.account.buy_shares("AAPL", 3)
        self.assertEqual(self.account.cash_balance, 700.0)
        self.assertEqual(self.account.get_holdings(), {"AAPL": 3})
        self.assertEqual(txn.price, 100.0)

    def test_buy_shares_cannot_exceed_cash(self):
        self.account.deposit(100.0)
        with self.assertRaises(ValueError):
            self.account.buy_shares("TSLA", 1)

    def test_sell_shares_updates_holdings_and_cash(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 3)
        txn = self.account.sell_shares("AAPL", 2)
        self.assertEqual(self.account.cash_balance, 900.0)
        self.assertEqual(self.account.get_holdings(), {"AAPL": 1})
        self.assertEqual(txn.type, "sell")

    def test_sell_shares_cannot_exceed_holdings(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 1)
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 2)

    def test_portfolio_value_calculation(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        self.assertEqual(self.account.get_portfolio_value(), 1000.0)

    def test_profit_loss_calculation(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        self.assertEqual(self.account.get_profit_loss(), 0.0)
        self.account.sell_shares("AAPL", 1)
        self.assertEqual(self.account.get_profit_loss(), 0.0)

    def test_transaction_history_records_all_operations(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        self.account.sell_shares("AAPL", 1)
        self.account.withdraw(50.0)
        txns = self.account.get_transactions()
        self.assertEqual([t.type for t in txns], ["deposit", "buy", "sell", "withdraw"])

    def test_invalid_amounts_rejected(self):
        for amount in [0, -1]:
            with self.assertRaises(ValueError):
                self.account.deposit(amount)
            with self.assertRaises(ValueError):
                self.account.withdraw(amount)

    def test_invalid_quantities_rejected(self):
        self.account.deposit(1000.0)
        for quantity in [0, -1]:
            with self.assertRaises(ValueError):
                self.account.buy_shares("AAPL", quantity)
            with self.assertRaises(ValueError):
                self.account.sell_shares("AAPL", quantity)
        with self.assertRaises(ValueError):
            self.account.buy_shares("", 1)
        with self.assertRaises(ValueError):
            self.account.buy_shares("MSFT", 1)
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 1)


if __name__ == "__main__":
    unittest.main()
```

Unit test results: 13 tests ran, 0 failures, 0 errors.