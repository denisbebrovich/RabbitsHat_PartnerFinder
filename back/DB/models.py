from sqlalchemy import Boolean, Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Company(Base):
    __tablename__ = 'companies'
    hh_id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    is_it_company = Column(Boolean)
    industries = Column(JSON)
    region = Column(String(100))
    tech_stack = Column(JSON)
    description = Column(Text)
    site_url = Column(String(500))
    score = Column(Float, default=0.0)

    vacancies = relationship("Vacancy", back_populates="company")
    emails = relationship("Email", back_populates="company")

class Vacancy(Base):
    __tablename__ = 'vacancies'
    hh_id = Column(String, primary_key=True)
    title = Column(String(500))
    company_id = Column(String, ForeignKey('companies.hh_id'))
    description = Column(Text)
    source = Column(String(100), default='hh.ru')
    requirements = Column(JSON)
    experience = Column(String(100))
    employment = Column(String(100))
    location = Column(String(100))
    professional_role = Column(String(200))
    published_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="vacancies")


class Email(Base):
    __tablename__ = 'emails'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey('companies.hh_id'))

    content = Column(Text)
    # Вот эти поля должны быть:
    final_content = Column(Text, nullable=True)
    status = Column(String(50), default='generated')
    is_approved = Column(Boolean, default=False)
    human_feedback = Column(Text, nullable=True)
    generation_params = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="emails")