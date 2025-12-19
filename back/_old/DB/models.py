from sqlalchemy import Boolean, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class Company(Base):
    __tablename__='companies'
    hh_id = Column(String, primary_key = True)
    name = Column(String(255), nullable = False)
    is_it_company = Column(Boolean)
    industries = Column(JSON)
    region = Column(String(100))
    tech_stack = Column(JSON)
    description = Column(Text)
    site_url = Column(String(500))
    
    vacancies = relationship("Vacancy", back_populates="company")

class Vacancy(Base):
    __tablename__='vacancies'
    hh_id = Column(String, primary_key = True)
    title = Column(String(500))
    company_id = Column(String, ForeignKey('companies.hh_id'))
    description = Column(Text)
    source = Column(String(100), default='hh.ru')
    requirements = Column(JSON)
    experience = Column(String(100))
    employment = Column(String(100))
    location = Column(String(100))
    professional_role = Column(String(200))
    published_at = Column(DateTime, default = datetime.utcnow)
    
    company = relationship("Company", back_populates="vacancies")