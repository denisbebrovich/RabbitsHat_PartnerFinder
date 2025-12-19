from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List
import os
from DB.models import Memory

from DB.models import Company, Email, Vacancy

router = APIRouter(prefix="/api")

POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql://admin:password@localhost:5432')
DB_URL = f"{POSTGRES_URL}/partner_finder"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TechStackUpdate(BaseModel):
    tech_stack: List[str]


class EmailDraft(BaseModel):
    company_id: str
    content: str
    status: str
    is_approved: bool


class SkipLog(BaseModel):
    company_id: str
    reason: str

class MemoryItem(BaseModel):
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0

@router.get("/agent/next_task")
def get_next_task(db: Session = Depends(get_db)):
    company = db.query(Company).outerjoin(Email).filter(Email.id == None).first()

    if not company:
        return None

    vacancies_text = [v.description for v in company.vacancies if v.description]

    return {
        "hh_id": company.hh_id,
        "name": company.name,
        "tech_stack": company.tech_stack or [],
        "is_it_company": company.is_it_company,
        "description": company.description,
        "vacancies_text": vacancies_text
    }


@router.patch("/companies/{company_id}")
def update_company_stack(company_id: str, data: TechStackUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.hh_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.tech_stack = data.tech_stack
    db.commit()
    return {"status": "updated", "stack_size": len(data.tech_stack)}


@router.post("/emails")
def save_email(data: EmailDraft, db: Session = Depends(get_db)):
    existing = db.query(Email).filter(Email.company_id == data.company_id).first()

    if existing:
        existing.content = data.content
        existing.status = data.status
        existing.is_approved = data.is_approved
        if data.is_approved:
            existing.final_content = data.content
    else:
        new_email = Email(
            company_id=data.company_id,
            content=data.content,
            final_content=data.content if data.is_approved else None,
            status=data.status,
            is_approved=data.is_approved
        )
        db.add(new_email)

    db.commit()
    return {"status": "saved"}


@router.get("/memories/{company_id}")
def get_company_memories(company_id: str, db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.company_id == company_id).all()

    return [
        {
            "subject": m.subject,
            "predicate": m.predicate,
            "object": m.obj,
            "confidence": m.confidence
        }
        for m in memories
    ]


@router.post("/memories/{company_id}")
def add_memory(company_id: str, memory: MemoryItem, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.hh_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    existing = db.query(Memory).filter(
        Memory.company_id == company_id,
        Memory.subject == memory.subject,
        Memory.predicate == memory.predicate,
        Memory.obj == memory.obj
    ).first()

    if existing:
        return {"status": "already_exists"}

    new_memory = Memory(
        company_id=company_id,
        subject=memory.subject,
        predicate=memory.predicate,
        obj=memory.obj,
        confidence=memory.confidence
    )
    db.add(new_memory)
    db.commit()

    return {"status": "saved", "fact": f"{memory.subject} {memory.predicate} {memory.obj}"}