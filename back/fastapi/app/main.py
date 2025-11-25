from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DB.models import Company, Vacancy
import json

app = FastAPI()

db_url = 'postgresql://admin:password@postgres:5432/partner_finder'
engine = create_engine(db_url)
Session = sessionmaker(bind = engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/db/companies")
async def companies():
    with Session() as session:
        return [json.dumps(company) for company in session.query(Company).all()]


# health
# docs
# ну и мэйн 
# и бд
