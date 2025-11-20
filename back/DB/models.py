from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Company(Base):
  __tablename__='Companies'
  id = Column(integer, primary_key = True, index = True)
  name = Column(String(255), nullable = False)
  industry = Column(String(100))
  size = Column(String(100))
  region = Column(String(100))
  tech_stack = Column(JSON)
  
