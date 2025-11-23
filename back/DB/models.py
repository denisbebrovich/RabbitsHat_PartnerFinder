from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Company(Base):
  __tablename__='Companies'
  id = Column(Integer, primary_key = True, index = True)
  name = Column(String(255), nullable = False)
  industry = Column(String(100))
  size = Column(String(100))
  region = Column(String(100))
  tech_stack = Column(JSON)
  
class Vacancy(Base):
  __tablename__='Vacancies'
  id = Column(Integer, primary_key = True, index = True)
  title = Column(String(500))
  description = Column(Text)
  source = Column(String(50))
  requirements = Column(JSON)
  company_id = Column(Integer)
  created_at = Column(DateTime, default = datetime.utcnow)

class Email(Base):
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key = True, index = True)
    company_id = Column(Integer)
    content = Column(Text)
    status = Column(String(50), default = 'draft')
    created_at = Column(DateTime, default = datetime.utcnow)