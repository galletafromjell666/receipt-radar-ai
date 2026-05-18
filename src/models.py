from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Session, relationship

from src.database import Base

DEFAULT_CATEGORIES = [
    "Food",
    "Gifts",
    "Other",
    "Shopping",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Transport",
    "Beauty",
]


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    merchant = Column(String)
    source = Column(String)
    account = Column(String)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="expenses")


class RecurrentExpense(Base):
    __tablename__ = "recurrent_expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    merchant = Column(String)
    source = Column(String)
    account = Column(String)
    description = Column(Text)
    last_applied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")


def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    for name in DEFAULT_CATEGORIES:
        db.add(Category(name=name, is_editable=False))
    db.commit()
