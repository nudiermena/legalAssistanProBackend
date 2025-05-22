from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PastCase(Base):
    __tablename__ = 'past_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_type = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    outcome = Column(String, nullable=False)  # 'favorable' or 'desfavorable'
    awarded_amount = Column(Float, nullable=True)
    resolution_time_months = Column(Integer, nullable=True)
    date = Column(Date, nullable=True)
    summary = Column(String, nullable=True)
    employee_favorable = Column(Boolean, nullable=True) 