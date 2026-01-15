"""
AccountHistory model for tracking account events and balances.

This model stores:
- Account balance snapshots
- Credits and debits
- Margin utilization
- Broker fees and charges
- Account events (deposits, withdrawals, etc.)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.schema import Index
import enum

from src.database.base import Base, TimestampMixin, PrimaryKeyMixin


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    TRADE_PROFIT = "trade_profit"
    TRADE_LOSS = "trade_loss"
    BROKERAGE = "brokerage"
    TAXES = "taxes"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


class AccountHistory(Base, PrimaryKeyMixin, TimestampMixin):
    """
    AccountHistory model for storing account transactions and balance snapshots.
    
    Attributes:
        id: Primary key
        
        # Transaction Details
        transaction_date: Date of transaction
        transaction_type: Type of transaction
        transaction_id: Unique transaction identifier
        
        # Amount Details
        amount: Transaction amount (positive for credit, negative for debit)
        currency: Currency code (INR, USD, etc.)
        
        # Balance Details
        balance_before: Account balance before transaction
        balance_after: Account balance after transaction
        available_balance: Available balance (after margins)
        blocked_amount: Amount blocked for margins/pending orders
        
        # Margin Details
        margin_used: Margin currently utilized
        margin_available: Margin available
        margin_percentage: Margin utilization percentage
        
        # Related Information
        related_trade_id: Trade ID if related to a trade
        related_order_id: Order ID if related to an order
        
        # Description
        description: Transaction description
        notes: Additional notes
        
        # Broker Details
        broker_reference: Broker's reference number
        broker_fee: Broker fee for this transaction
        taxes_paid: Taxes paid for this transaction
        
        # Paper Trading Flag
        is_paper_trading: Paper trading flag
        
        # Timestamps
        created_at: Record creation time
        updated_at: Record update time
    """
    
    __tablename__ = "account_history"
    
    # Transaction Details
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Amount Details
    amount = Column(Float, nullable=False)  # Positive = credit, Negative = debit
    currency = Column(String(10), default="INR")
    
    # Balance Details
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=True)
    blocked_amount = Column(Float, default=0.0)
    
    # Margin Details
    margin_used = Column(Float, default=0.0)
    margin_available = Column(Float, nullable=True)
    margin_percentage = Column(Float, default=0.0)
    
    # Related Information
    related_trade_id = Column(String(100), nullable=True, index=True)
    related_order_id = Column(String(100), nullable=True)
    
    # Description
    description = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Broker Details
    broker_reference = Column(String(100), nullable=True)
    broker_fee = Column(Float, default=0.0)
    taxes_paid = Column(Float, default=0.0)
    
    # Paper Trading Flag
    is_paper_trading = Column(Boolean, default=False, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_account_date_type', 'transaction_date', 'transaction_type'),
        Index('idx_account_trade', 'related_trade_id'),
    )
    
    def __repr__(self):
        return (
            f"<AccountHistory(id={self.id}, date={self.transaction_date}, "
            f"type={self.transaction_type}, amount={self.amount}, "
            f"balance={self.balance_after})>"
        )
    
    def to_dict(self):
        """Convert account history record to dictionary."""
        return {
            "id": self.id,
            "transaction": {
                "date": self.transaction_date.isoformat() if self.transaction_date else None,
                "type": self.transaction_type.value if self.transaction_type else None,
                "id": self.transaction_id,
                "amount": self.amount,
                "currency": self.currency,
            },
            "balance": {
                "before": self.balance_before,
                "after": self.balance_after,
                "available": self.available_balance,
                "blocked": self.blocked_amount,
            },
            "margin": {
                "used": self.margin_used,
                "available": self.margin_available,
                "percentage": self.margin_percentage,
            },
            "related": {
                "trade_id": self.related_trade_id,
                "order_id": self.related_order_id,
            },
            "details": {
                "description": self.description,
                "notes": self.notes,
            },
            "broker": {
                "reference": self.broker_reference,
                "fee": self.broker_fee,
                "taxes": self.taxes_paid,
            },
            "metadata": {
                "is_paper_trading": self.is_paper_trading,
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            }
        }
