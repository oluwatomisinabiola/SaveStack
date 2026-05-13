"""
Tests for the pure ledger math.

These tests have no database, no HTTP, no external services.
They prove the math is correct in isolation, so when we plug
the ledger into the webhook handler later, we trust the math
and can focus debugging on the surrounding concerns.
"""
from decimal import Decimal

import pytest

from app.services.ledger import compute_deposit_plan


# ---------- Happy path: typical allocations ----------

def test_deposit_with_30_percent_allocation_splits_correctly():
    """A $100 deposit with 30% allocation produces $70 cash, $30 to crypto."""
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=30,
        btc_price=Decimal("67000.00"),
    )

    assert plan.cash_amount == Decimal("70.00")
    assert plan.crypto_usd_amount == Decimal("30.00")
    assert len(plan.entries) == 3  # cash deposit + cash debit + crypto credit


def test_deposit_with_zero_percent_allocation_is_all_cash():
    """A $100 deposit with 0% allocation produces only a cash entry."""
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=0,
        btc_price=Decimal("67000.00"),
    )

    assert plan.cash_amount == Decimal("100.00")
    assert plan.crypto_usd_amount == Decimal("0")
    assert plan.btc_amount_purchased == Decimal("0")
    assert len(plan.entries) == 1  # only the cash deposit entry
    assert plan.entries[0].account_type == "cash"
    assert plan.entries[0].amount == Decimal("100.00")


def test_deposit_with_100_percent_allocation_is_all_crypto():
    """A $100 deposit with 100% allocation: cash deposit + full debit to crypto."""
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=100,
        btc_price=Decimal("50000.00"),
    )

    assert plan.cash_amount == Decimal("0.00")
    assert plan.crypto_usd_amount == Decimal("100.00")
    assert plan.btc_amount_purchased == Decimal("0.00200000")
    assert len(plan.entries) == 3


# ---------- BTC quantity math ----------

def test_btc_amount_computed_correctly():
    """$30 at BTC=$67,000 should buy 0.00044776 BTC (8-decimal precision)."""
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=30,
        btc_price=Decimal("67000.00"),
    )

    # 30 / 67000 = 0.000447761194... -> quantized down to 0.00044776
    assert plan.btc_amount_purchased == Decimal("0.00044776")


def test_btc_amount_uses_round_down_not_round_half_even():
    """Rounding should be ROUND_DOWN — we never grant more BTC than the math gives."""
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=50,
        btc_price=Decimal("33333.33"),
    )

    # 50 / 33333.33 = 0.00150000015... -> ROUND_DOWN to 0.00150000
    assert plan.btc_amount_purchased == Decimal("0.00150000")


# ---------- The invariant: entries balance ----------

def test_entries_sum_to_zero_in_net_balance():
    """
    For any deposit, the cash entries net to (deposit - crypto_usd)
    and the crypto entries net to crypto_usd.
    Sum of all entries should equal the original deposit amount.
    """
    plan = compute_deposit_plan(
        amount_usd=Decimal("250.00"),
        allocation_pct_crypto=40,
        btc_price=Decimal("67000.00"),
    )

    total_change = sum(entry.amount for entry in plan.entries)
    assert total_change == Decimal("250.00")

    cash_total = sum(e.amount for e in plan.entries if e.account_type == "cash")
    crypto_total = sum(e.amount for e in plan.entries if e.account_type == "crypto")

    assert cash_total == plan.cash_amount
    assert crypto_total == plan.crypto_usd_amount


# ---------- Decimal precision ----------

def test_no_float_drift_for_one_third():
    """
    A 33% allocation of $100 should produce exactly $33.00 to crypto,
    not $33.000000000004 or similar float noise.
    """
    plan = compute_deposit_plan(
        amount_usd=Decimal("100.00"),
        allocation_pct_crypto=33,
        btc_price=Decimal("67000.00"),
    )

    assert plan.crypto_usd_amount == Decimal("33.00")
    assert plan.cash_amount == Decimal("67.00")


# ---------- Bad inputs ----------

def test_negative_deposit_raises():
    with pytest.raises(ValueError, match="amount_usd must be positive"):
        compute_deposit_plan(
            amount_usd=Decimal("-50"),
            allocation_pct_crypto=30,
            btc_price=Decimal("67000.00"),
        )


def test_zero_deposit_raises():
    with pytest.raises(ValueError, match="amount_usd must be positive"):
        compute_deposit_plan(
            amount_usd=Decimal("0"),
            allocation_pct_crypto=30,
            btc_price=Decimal("67000.00"),
        )


def test_allocation_over_100_raises():
    with pytest.raises(ValueError, match="allocation_pct_crypto"):
        compute_deposit_plan(
            amount_usd=Decimal("100"),
            allocation_pct_crypto=150,
            btc_price=Decimal("67000.00"),
        )


def test_negative_allocation_raises():
    with pytest.raises(ValueError, match="allocation_pct_crypto"):
        compute_deposit_plan(
            amount_usd=Decimal("100"),
            allocation_pct_crypto=-10,
            btc_price=Decimal("67000.00"),
        )


def test_zero_btc_price_raises():
    with pytest.raises(ValueError, match="btc_price must be positive"):
        compute_deposit_plan(
            amount_usd=Decimal("100"),
            allocation_pct_crypto=30,
            btc_price=Decimal("0"),
        )