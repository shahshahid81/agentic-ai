# Trading Simulation Platform — Account Management System Design

## 1. Overview

Build a simple in-memory account management system for a trading simulation platform that supports:

- Creating a user account
- Depositing funds
- Withdrawing funds
- Buying shares
- Selling shares
- Calculating portfolio value
- Calculating profit/loss from initial deposit
- Reporting holdings at any point in time
- Reporting profit/loss at any point in time
- Listing all transactions over time
- Preventing invalid balance / holdings operations

The system depends on an existing function:

- `get_share_price(symbol)`  
  Returns the current price for a symbol. Test implementation returns fixed prices for `AAPL`, `TSLA`, `GOOGL`.

All files live in the same directory.

---

## 2. Proposed File Layout

Since there is no subdirectory structure, use the following files in the same directory:

- `backend.py` — backend domain logic and account service
- `app.py` — Gradio UI
- `test_backend.py` — unit tests

---

## 3. Domain Model

### Core Concepts

- **Account**
  - Single trading simulation account
  - Tracks:
    - cash balance
    - initial deposits total
    - holdings by symbol
    - transaction history
- **Transaction**
  - Records every state-changing operation
  - Includes deposits, withdrawals, buys, sells
- **Holding**
  - Represents quantity owned per stock symbol
- **Valuation**
  - Portfolio value = cash balance + current market value of holdings
  - Profit/Loss = portfolio value - total initial deposits

---

## 4. Backend Design

## 4.1 Module: `backend.py`

### Responsibility

Implement all business logic, validation, transaction recording, and reporting.

### Dependencies

- Standard library only
- Existing `get_share_price(symbol)` function available in same directory or injected dependency for testability

---

## 4.2 Constants / Types

### Supported transaction types

- `"deposit"`
- `"withdraw"`
- `"buy"`
- `"sell"`

### Suggested validation rules

- Deposit amount must be positive
- Withdrawal amount must be positive
- Withdrawal cannot exceed available cash
- Buy quantity must be positive
- Sell quantity must be positive
- Buy requires sufficient cash
- Sell requires sufficient shares of the symbol
- Symbol must be non-empty string
- Portfolio valuation should use latest `get_share_price(symbol)`

---

## 4.3 Data Structures

### `Transaction` dataclass

**Purpose:** immutable record of each action.

**Fields:**
- `timestamp: str`
- `type: str`
- `symbol: str | None`
- `quantity: int | None`
- `amount: float | None`
- `price: float | None`
- `cash_balance_after: float`
- `note: str | None`

---

### `Holding` dataclass

**Purpose:** aggregate quantity for a symbol.

**Fields:**
- `symbol: str`
- `quantity: int`

---

## 4.4 Main Class

### `AccountManager`

**Purpose:** primary interface for account operations.

### State

- `cash_balance: float`
- `initial_deposits_total: float`
- `holdings: dict[str, int]`
- `transactions: list[Transaction]`

### Constructor

#### `__init__(self, price_provider=get_share_price) -> None`

- `price_provider` is a callable used to look up share prices
- Enables test injection

---

## 4.5 Public Methods and Signatures

### Account lifecycle

#### `create_account(self) -> None`
- Initializes or resets the account
- Clears holdings and transactions
- Resets cash balance and initial deposit total

---

### Cash operations

#### `deposit(self, amount: float) -> Transaction`
- Adds cash to balance
- Increases `initial_deposits_total`
- Records transaction

#### `withdraw(self, amount: float) -> Transaction`
- Removes cash from balance
- Fails if resulting balance would be negative
- Records transaction

---

### Trading operations

#### `buy_shares(self, symbol: str, quantity: int) -> Transaction`
- Looks up current price using `price_provider(symbol)`
- Validates enough cash is available
- Decreases cash balance by `price * quantity`
- Increases holdings quantity
- Records transaction

#### `sell_shares(self, symbol: str, quantity: int) -> Transaction`
- Validates enough shares are held
- Looks up current price using `price_provider(symbol)`
- Increases cash balance by `price * quantity`
- Decreases holdings quantity
- Removes symbol from holdings if quantity reaches zero
- Records transaction

---

### Reporting

#### `get_holdings(self) -> dict[str, int]`
- Returns current holdings snapshot

#### `get_transactions(self) -> list[Transaction]`
- Returns transaction history in chronological order

#### `get_portfolio_value(self) -> float`
- Returns cash balance plus market value of all holdings

#### `get_profit_loss(self) -> float`
- Returns `get_portfolio_value() - initial_deposits_total`

#### `get_account_summary(self) -> dict[str, object]`
- Convenience summary for UI
- Should include:
  - cash balance
  - initial deposits total
  - portfolio value
  - profit/loss
  - holdings
  - transaction count

---

## 4.6 Helper Methods

These can be private methods inside `AccountManager`.

#### `_validate_positive_amount(self, amount: float, field_name: str) -> None`
#### `_validate_positive_quantity(self, quantity: int, field_name: str) -> None`
#### `_get_price(self, symbol: str) -> float`
#### `_record_transaction(...) -> Transaction`
#### `_format_timestamp(self) -> str`

---

## 4.7 Error Handling

Use `ValueError` for all invalid user actions.

### Error cases

- Deposit amount <= 0
- Withdrawal amount <= 0
- Withdrawal exceeds balance
- Buy quantity <= 0
- Buy not affordable
- Sell quantity <= 0
- Sell more than holdings
- Invalid symbol input
- Unknown price symbol from provider

### Error messages

Keep them user-friendly and explicit, such as:

- `"Deposit amount must be positive"`
- `"Insufficient cash balance for withdrawal"`
- `"Insufficient cash balance for purchase"`
- `"Insufficient shares of AAPL to sell"`

---

## 4.8 Backend Function Signatures

If a functional style is preferred for some parts, these are acceptable helper signatures:

#### `get_share_price(symbol: str) -> float`
- External dependency already provided

#### `format_currency(amount: float) -> str`
- Optional helper for UI display only

#### `serialize_transactions(transactions: list[Transaction]) -> list[dict[str, object]]`
- Optional helper for UI display

---

## 5. Gradio Frontend Design

## 5.1 Module: `app.py`

### Responsibility

Provide a simple UI for account creation, deposit/withdraw, buy/sell, and reporting.

### Gradio 6 guidance for frontend engineer

Use Gradio 6 `Blocks` and component event handlers.

Important API notes for Gradio 6:

1. **Use `gr.Blocks()` as the root layout**
2. **Attach events with `.click(...)` / `.change(...)` / `.load(...)`**
3. **Event handlers can use `inputs_kwargs` in Gradio 6** if keyword mapping is needed, but positional `inputs` is fine for this app
4. **`launch()` signature includes**:
   - `server_name`
   - `server_port`
   - `share`
   - `show_error`
   - `prevent_thread_lock`
   - `inbrowser`
5. Prefer returning component values directly from event handlers rather than using older update patterns where possible
6. Use `gr.Textbox`, `gr.Number`, `gr.Dropdown`, `gr.Button`, `gr.Dataframe`, `gr.Markdown`, `gr.Accordion`, `gr.Row`, `gr.Column`, `gr.Tabs`, `gr.Tab`

### UI behavior recommendation

- One account instance held in app state
- Buttons for:
  - Create/Reset account
  - Deposit
  - Withdraw
  - Buy shares
  - Sell shares
  - Refresh summary
- Display sections for:
  - cash balance
  - initial deposits
  - portfolio value
  - profit/loss
  - holdings
  - transactions

---

## 5.2 UI State Strategy

Use a hidden `gr.State` component to store the `AccountManager` instance.

### State component

- `account_state = gr.State(...)`

### Event flow

- Create account initializes state
- Each action handler reads state, calls backend method, returns:
  - updated state
  - summary fields
  - holdings table
  - transaction table
  - status message

---

## 5.3 Proposed Frontend Layout

### Top-level structure

- `gr.Markdown` title and short instructions
- `gr.Tabs`
  - `Account`
  - `Trading`
  - `Reports`

### Account tab

Inputs:
- Create/reset button
- Optional informational text

Outputs:
- status message
- summary snapshot

### Trading tab

Deposit section:
- `gr.Number(label="Deposit Amount", minimum=0)`
- `gr.Button("Deposit")`

Withdraw section:
- `gr.Number(label="Withdraw Amount", minimum=0)`
- `gr.Button("Withdraw")`

Buy section:
- `gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Buy Symbol")`
- `gr.Number(label="Quantity", minimum=1, precision=0)`
- `gr.Button("Buy")`

Sell section:
- `gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Sell Symbol")`
- `gr.Number(label="Quantity", minimum=1, precision=0)`
- `gr.Button("Sell")`

### Reports tab

Outputs:
- `gr.Markdown` for account summary
- `gr.Dataframe` for holdings
- `gr.Dataframe` for transactions
- optional `gr.JSON` if desired, but not required

---

## 5.4 Frontend Function Signatures

### State/action handlers

#### `initialize_account() -> tuple[AccountManager, str, dict[str, object], list[list[object]], list[list[object]]]`
- Creates a new account and returns updated UI payload

#### `handle_deposit(account: AccountManager, amount: float) -> tuple[...]`
#### `handle_withdraw(account: AccountManager, amount: float) -> tuple[...]`
#### `handle_buy(account: AccountManager, symbol: str, quantity: int) -> tuple[...]`
#### `handle_sell(account: AccountManager, symbol: str, quantity: int) -> tuple[...]`
#### `refresh_view(account: AccountManager) -> tuple[...]`

Each handler should return:
- updated account state
- status message
- summary data
- holdings table data
- transactions table data

---

## 5.5 Gradio 6 API Guidance for Specific Components

### `gr.Blocks()`
Use as the main container:

- `with gr.Blocks() as demo:`

### `gr.Button`
Use:

- `button = gr.Button("Label")`
- `button.click(fn=handler, inputs=[...], outputs=[...])`

### `gr.Number`
Use for amounts and quantities.

Recommended kwargs:
- `label=...`
- `value=...`
- `minimum=...`
- `precision=0` for integer-like quantities

### `gr.Dropdown`
Use for symbols.

Recommended kwargs:
- `choices=["AAPL", "TSLA", "GOOGL"]`
- `label="Symbol"`
- `value="AAPL"` or `None`

### `gr.Dataframe`
Use for holdings and transactions display.

Recommended use:
- output only
- pass a list of rows, or a pandas-like table shape if available
- keep output as plain tabular data; no dependency on pandas required

### `gr.Markdown`
Use for:
- page title
- summary
- status/error messages

### `gr.Accordion`
Optional for transaction list and raw details.

### `gr.Tabs` / `gr.Tab`
Use to separate action and reporting areas.

### `launch()`
Recommended call:

- `demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)`

If sandbox behavior requires it, use:

- `prevent_thread_lock=True`

---

## 6. Test Design

## 6.1 Module: `test_backend.py`

### Responsibility

Unit test the backend logic only. Do not test Gradio UI here.

### Approach

Use a fake share-price provider to avoid relying on external data.

---

## 6.2 Test Fixture / Helper

#### `fake_price_provider(symbol: str) -> float`
Fixed test values:
- `AAPL` -> `100.0`
- `TSLA` -> `200.0`
- `GOOGL` -> `150.0`

Unknown symbols should raise `KeyError` or `ValueError` depending on backend contract.

---

## 6.3 Test Cases

### Account creation
- New account starts with:
  - zero cash
  - zero holdings
  - empty transactions
  - zero initial deposits

### Deposit
- Deposit increases cash balance
- Deposit increases initial deposits total
- Transaction recorded

### Withdraw
- Withdraw decreases cash balance
- Withdraw cannot exceed balance
- Invalid withdrawal raises `ValueError`

### Buy shares
- Buying with enough cash succeeds
- Cash decreases by market value
- Holdings increase
- Transaction recorded

### Sell shares
- Selling owned shares succeeds
- Cash increases by market value
- Holdings decrease
- Selling too many shares raises `ValueError`

### Portfolio value
- Correctly computes cash + holdings market value

### Profit/loss
- Correctly computes value minus initial deposits

### Transaction history
- Transaction list preserves order and includes all operations

### Edge cases
- Zero or negative deposit/withdraw amount rejected
- Zero or negative quantity rejected
- Attempt to buy more than affordable rejected
- Attempt to sell nonexistent symbol rejected
- Attempt to sell more than owned rejected

---

## 6.4 Test Function Signatures

#### `test_create_account_initial_state() -> None`
#### `test_deposit_updates_balance_and_initial_deposit() -> None`
#### `test_withdraw_updates_balance() -> None`
#### `test_withdraw_cannot_overdraw() -> None`
#### `test_buy_shares_updates_holdings_and_cash() -> None`
#### `test_buy_shares_cannot_exceed_cash() -> None`
#### `test_sell_shares_updates_holdings_and_cash() -> None`
#### `test_sell_shares_cannot_exceed_holdings() -> None`
#### `test_portfolio_value_calculation() -> None`
#### `test_profit_loss_calculation() -> None`
#### `test_transaction_history_records_all_operations() -> None`
#### `test_invalid_amounts_rejected() -> None`
#### `test_invalid_quantities_rejected() -> None`

---

## 7. Assignment to Engineers

## 7.1 `backend_engineer`

### Deliverable
Implement `backend.py`

### Scope
- `Transaction` dataclass
- `Holding` dataclass
- `AccountManager` class
- validation logic
- transaction recording
- portfolio and P/L calculations
- reporting helpers

### Acceptance criteria
- All required operations work
- Invalid operations raise `ValueError`
- Backend is deterministic under injected price provider
- All methods are testable without UI

---

## 7.2 `frontend_engineer`

### Deliverable
Implement `app.py`

### Scope
- Gradio 6 `Blocks` UI
- account state handling via `gr.State`
- forms for deposit/withdraw/buy/sell
- holdings and transactions reporting
- status/error output
- launch configuration

### Acceptance criteria
- UI can create/reset account
- UI can execute deposit/withdraw/buy/sell
- UI shows updated summary, holdings, and transactions
- UI uses correct Gradio 6 patterns and signatures
- No dependency on unavailable packages

### Gradio 6 notes to follow
- Use `Blocks`, `Tabs`, `Tab`, `Row`, `Column`
- Use `.click(...)` for actions
- Use `show_error=True` during launch in development
- Prefer direct return values from handlers
- If passing inputs by name is helpful, Gradio 6 supports `inputs_kwargs`, but it is not required here

---

## 7.3 `test_engineer`

### Deliverable
Implement `test_backend.py`

### Scope
- Unit tests for all backend functionality
- Fake share price provider
- Validation of calculations and error handling

### Acceptance criteria
- Full coverage of core behaviors
- Tests verify transaction logging and reporting
- Tests do not require Gradio or network access

---

## 8. Suggested Method Contracts

Below is the consolidated contract list for implementation.

### `backend.py`

#### `class Transaction`
- `timestamp: str`
- `type: str`
- `symbol: str | None`
- `quantity: int | None`
- `amount: float | None`
- `price: float | None`
- `cash_balance_after: float`
- `note: str | None`

#### `class Holding`
- `symbol: str`
- `quantity: int`

#### `class AccountManager`
- `__init__(self, price_provider=get_share_price) -> None`
- `create_account(self) -> None`
- `deposit(self, amount: float) -> Transaction`
- `withdraw(self, amount: float) -> Transaction`
- `buy_shares(self, symbol: str, quantity: int) -> Transaction`
- `sell_shares(self, symbol: str, quantity: int) -> Transaction`
- `get_holdings(self) -> dict[str, int]`
- `get_transactions(self) -> list[Transaction]`
- `get_portfolio_value(self) -> float`
- `get_profit_loss(self) -> float`
- `get_account_summary(self) -> dict[str, object]`

### `app.py`

- `initialize_account() -> tuple[...]`
- `handle_deposit(account, amount) -> tuple[...]`
- `handle_withdraw(account, amount) -> tuple[...]`
- `handle_buy(account, symbol, quantity) -> tuple[...]`
- `handle_sell(account, symbol, quantity) -> tuple[...]`
- `refresh_view(account) -> tuple[...]`
- `build_app() -> gr.Blocks`
- `main() -> None`

### `test_backend.py`

- test functions as listed above

---

## 9. Implementation Notes

- Keep logic in backend and UI thin
- Do not duplicate pricing or portfolio rules in Gradio code
- Ensure all currency math is handled consistently as floats
- Use consistent rounding/formatting in UI only; backend should preserve raw values
- Keep transactions append-only and chronological
- Prefer explicit, readable error messages
- In the UI, map holdings and transactions into simple row lists for display

---

## 10. Success Criteria

The system is complete when:

- A user can create an account
- A user can deposit funds
- A user can withdraw funds within balance
- A user can buy shares within available cash
- A user can sell only owned shares
- Portfolio value and profit/loss are correctly computed
- Holdings and transactions are reportable at any point
- Unit tests cover all backend behavior
- Gradio app launches successfully in the sandbox using Gradio 6 APIs