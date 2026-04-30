from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True) # Essential for deduplication
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    category = Column(String)
    merchant = Column(String)
    source = Column(String)
    account = Column(String)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow, index=True) # Essential for sorting
    raw_email_body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
