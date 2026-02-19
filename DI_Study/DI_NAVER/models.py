from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class SearchKeyword(Base):
    __tablename__ = "search_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NewsData(Base):
    __tablename__ = "news_data"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    title = Column(String)
    link = Column(String, unique=True)
    description = Column(Text)
    pub_date = Column(DateTime)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

class TrendData(Base):
    __tablename__ = "trend_data"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, index=True)
    period_start = Column(String)
    period_end = Column(String)
    data_date = Column(String) # period within the data
    ratio = Column(Integer) # or Float, keeping simple
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
