from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from database import Base

class SalesFact(Base):
    __tablename__ = "sales_facts"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String, index=True) # e.g., 'US', 'DE'
    year_month = Column(String, index=True)   # e.g., '2025-10'
    section = Column(String) # 'market', 'product', 'size', 'price'
    category = Column(String) # 'total', 'breakdown'
    metric = Column(String) # 'sales', 'traffic', 'share_pct', 'sales_val'
    
    # For Breakdown
    brand = Column(String, nullable=True)
    
    # Value
    value = Column(Float)
    
    # Metadata
    date = Column(String) # ISO Date e.g. 2025-10-01

class Hitlist(Base):
    __tablename__ = "hitlists"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String, index=True)
    year_month = Column(String, index=True)
    section = Column(String)
    
    rank = Column(Integer)
    model = Column(String)
    asin = Column(String)
    brand = Column(String)
    inch = Column(String)
    type_ = Column(String) # Type
    sales = Column(Float)
    share_pct = Column(Float)
    mom_pct = Column(Float)
    qty = Column(Integer)
    asp = Column(Float)
    traffic = Column(Integer)
    cvr_pct = Column(Float)

class InsightSummary(Base):
    __tablename__ = "insight_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String, index=True)
    year_month = Column(String, index=True)
    section = Column(String)
    content = Column(String) # JSON list of bullets
