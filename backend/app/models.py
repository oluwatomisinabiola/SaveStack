from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    allocation_pct_crypto: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")
    deposits: Mapped[list["Deposit"]] = relationship(back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "cash" or "crypto"
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=Decimal("0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="accounts")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="account")


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    stripe_event_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    stripe_session_id: Mapped[str] = mapped_column(String, nullable=True)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    btc_price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    btc_amount_purchased: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="deposits")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="deposit")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    deposit_id: Mapped[int] = mapped_column(ForeignKey("deposits.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    entry_type: Mapped[str] = mapped_column(String, nullable=False)  # "deposit", "crypto_buy", etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="ledger_entries")
    deposit: Mapped["Deposit"] = relationship(back_populates="ledger_entries")