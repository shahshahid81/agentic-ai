from __future__ import annotations

import gradio as gr

from backend import AccountManager, format_currency, serialize_transactions


SYMBOL_CHOICES = ["AAPL", "TSLA", "GOOGL"]


def _summary_markdown(account: AccountManager) -> str:
    summary = account.get_account_summary()
    holdings = summary["holdings"]
    holdings_text = (
        ", ".join(f"{sym}: {qty}" for sym, qty in holdings.items()) or "None"
    )
    return (
        f"### Account Summary\n"
        f"- Cash balance: {format_currency(summary['cash_balance'])}\n"
        f"- Initial deposits: {format_currency(summary['initial_deposits_total'])}\n"
        f"- Portfolio value: {format_currency(summary['portfolio_value'])}\n"
        f"- Profit / Loss: {format_currency(summary['profit_loss'])}\n"
        f"- Holdings: {holdings_text}\n"
        f"- Transaction count: {summary['transaction_count']}"
    )


def _holdings_table(account: AccountManager):
    return [
        [symbol, quantity]
        for symbol, quantity in sorted(account.get_holdings().items())
    ]


def _transactions_table(account: AccountManager):
    rows = []
    for txn in serialize_transactions(account.get_transactions()):
        rows.append(
            [
                txn["timestamp"],
                txn["type"],
                txn["symbol"],
                txn["quantity"],
                txn["amount"],
                txn["price"],
                txn["cash_balance_after"],
                txn["note"],
            ]
        )
    return rows


def _payload(account: AccountManager, status: str):
    return (
        account,
        status,
        _summary_markdown(account),
        _holdings_table(account),
        _transactions_table(account),
    )


def initialize_account():
    account = AccountManager()
    account.create_account()
    return _payload(account, "Account created/reset successfully.")


def handle_deposit(account: AccountManager, amount: float):
    try:
        account.deposit(amount)
        return _payload(account, f"Deposited {format_currency(amount)} successfully.")
    except Exception as exc:
        return _payload(account, f"Error: {exc}")


def handle_withdraw(account: AccountManager, amount: float):
    try:
        account.withdraw(amount)
        return _payload(account, f"Withdrew {format_currency(amount)} successfully.")
    except Exception as exc:
        return _payload(account, f"Error: {exc}")


def handle_buy(account: AccountManager, symbol: str, quantity: int):
    try:
        account.buy_shares(symbol, quantity)
        return _payload(account, f"Bought {quantity} shares of {symbol} successfully.")
    except Exception as exc:
        return _payload(account, f"Error: {exc}")


def handle_sell(account: AccountManager, symbol: str, quantity: int):
    try:
        account.sell_shares(symbol, quantity)
        return _payload(account, f"Sold {quantity} shares of {symbol} successfully.")
    except Exception as exc:
        return _payload(account, f"Error: {exc}")


def refresh_view(account: AccountManager):
    return _payload(account, "Refreshed account view.")


def build_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("# Trading Simulation Platform")
        gr.Markdown("Manage a simple simulated trading account in memory.")

        account_state = gr.State(AccountManager())
        status = gr.Markdown()
        summary = gr.Markdown()
        holdings = gr.Dataframe(headers=["Symbol", "Quantity"], interactive=False)
        transactions = gr.Dataframe(
            headers=[
                "Timestamp",
                "Type",
                "Symbol",
                "Quantity",
                "Amount",
                "Price",
                "Cash After",
                "Note",
            ],
            interactive=False,
        )

        with gr.Tabs():
            with gr.Tab("Account"):
                create_btn = gr.Button("Create / Reset Account")
                create_btn.click(
                    initialize_account,
                    inputs=None,
                    outputs=[account_state, status, summary, holdings, transactions],
                )

            with gr.Tab("Trading"):
                with gr.Row():
                    deposit_amount = gr.Number(label="Deposit Amount", minimum=0)
                    deposit_btn = gr.Button("Deposit")
                deposit_btn.click(
                    handle_deposit,
                    inputs=[account_state, deposit_amount],
                    outputs=[account_state, status, summary, holdings, transactions],
                )

                with gr.Row():
                    withdraw_amount = gr.Number(label="Withdraw Amount", minimum=0)
                    withdraw_btn = gr.Button("Withdraw")
                withdraw_btn.click(
                    handle_withdraw,
                    inputs=[account_state, withdraw_amount],
                    outputs=[account_state, status, summary, holdings, transactions],
                )

                with gr.Row():
                    buy_symbol = gr.Dropdown(
                        choices=SYMBOL_CHOICES, label="Buy Symbol", value="AAPL"
                    )
                    buy_quantity = gr.Number(
                        label="Quantity", minimum=1, precision=0, value=1
                    )
                    buy_btn = gr.Button("Buy")
                buy_btn.click(
                    handle_buy,
                    inputs=[account_state, buy_symbol, buy_quantity],
                    outputs=[account_state, status, summary, holdings, transactions],
                )

                with gr.Row():
                    sell_symbol = gr.Dropdown(
                        choices=SYMBOL_CHOICES, label="Sell Symbol", value="AAPL"
                    )
                    sell_quantity = gr.Number(
                        label="Quantity", minimum=1, precision=0, value=1
                    )
                    sell_btn = gr.Button("Sell")
                sell_btn.click(
                    handle_sell,
                    inputs=[account_state, sell_symbol, sell_quantity],
                    outputs=[account_state, status, summary, holdings, transactions],
                )

            with gr.Tab("Reports"):
                refresh_btn = gr.Button("Refresh View")
                refresh_btn.click(
                    refresh_view,
                    inputs=[account_state],
                    outputs=[account_state, status, summary, holdings, transactions],
                )

        demo.load(
            refresh_view,
            inputs=[account_state],
            outputs=[account_state, status, summary, holdings, transactions],
        )
    return demo


def main() -> None:
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
    )


if __name__ == "__main__":
    main()
