"""
Pure ledger math: given a deposit, compute the entries that should be written.

This module has no database access. All inputs come in as arguments,
all outputs are returned as dataclasses. This makes the math trivially
unit-testable in isolation from the rest of the system.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


# How many decimal places to track for BTC quantity.
# 8 = standard Bitcoin precision (1 satoshi = 0.00000001 BTC).
BTC_QUANTIZE = Decimal("0.00000001")

# How many decimal places to track for USD.
# 2 = standard for displayed USD; we use 8 internally for ledger consistency.
USD_QUANTIZE = Decimal("0.01")


@dataclass(frozen=True)
class LedgerEntryDraft:
    """An entry we plan to write. Not yet a database row."""
    account_type: str  # "cash" or "crypto"
    amount: Decimal    # signed: + for credit (money in), - for debit (money out)
    entry_type: str    # "deposit", "crypto_buy"


@dataclass(frozen=True)
class DepositPlan:
    """The full plan for writing a deposit: the entries and the BTC quantity bought."""
    entries: list[LedgerEntryDraft]
    btc_amount_purchased: Decimal
    cash_amount: Decimal
    crypto_usd_amount: Decimal


def compute_deposit_plan(
    amount_usd: Decimal,
    allocation_pct_crypto: int,
    btc_price: Decimal,
) -> DepositPlan:
    """
    Given a deposit, compute the ledger entries to write.

    Rules:
    - allocation_pct_crypto of the deposit (0-100) buys BTC at the given price
    - The rest goes to cash
    - All math is done in Decimal for exact precision (no floats)
    - BTC quantity is quantized to 8 decimal places (1 satoshi)
    - USD amounts are quantized to 2 decimal places

    Returns a DepositPlan with the entries to insert and the BTC quantity bought.
    """
    if amount_usd <= 0:
        raise ValueError("amount_usd must be positive")
    if not 0 <= allocation_pct_crypto <= 100:
        raise ValueError("allocation_pct_crypto must be between 0 and 100")
    if btc_price <= 0:
        raise ValueError("btc_price must be positive")

    # Split the deposit
    allocation = Decimal(allocation_pct_crypto) / Decimal(100)
    crypto_usd_amount = (amount_usd * allocation).quantize(USD_QUANTIZE, rounding=ROUND_DOWN)
    cash_amount = amount_usd - crypto_usd_amount

    # Compute BTC quantity (only if any crypto allocation)
    if crypto_usd_amount > 0:
        btc_amount = (crypto_usd_amount / btc_price).quantize(BTC_QUANTIZE, rounding=ROUND_DOWN)
    else:
        btc_amount = Decimal("0")

    # Build the entries
    entries: list[LedgerEntryDraft] = []

    # Always credit cash with the full deposit (the user's USD came in)
    entries.append(LedgerEntryDraft(
        account_type="cash",
        amount=amount_usd,
        entry_type="deposit",
    ))

    # If any allocation to crypto, debit cash and credit crypto
    if crypto_usd_amount > 0:
        entries.append(LedgerEntryDraft(
            account_type="cash",
            amount=-crypto_usd_amount,
            entry_type="crypto_buy",
        ))
        entries.append(LedgerEntryDraft(
            account_type="crypto",
            amount=crypto_usd_amount,
            entry_type="crypto_buy",
        ))

    return DepositPlan(
        entries=entries,
        btc_amount_purchased=btc_amount,
        cash_amount=cash_amount,
        crypto_usd_amount=crypto_usd_amount,
    )