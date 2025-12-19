from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DB.models import Company, Vacancy
from DB.init_database import init_database
from services.hh_etl import HHExtractor
import os
from api.data_endps import router as api_router

app = FastAPI()
app.include_router(api_router)
postgres_url = os.environ.get('POSTGRES_URL', 'postgresql://admin:password@localhost:5432')
db_url = postgres_url + '/partner_finder'

engine = create_engine(db_url)
Session = sessionmaker(bind = engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/db/companies")
async def db_companies(id=None):
    with Session() as session:
        if id != None:
            return session.query(Company).filter_by(hh_id=id).all()
        return session.query(Company).all()
    
@app.get("/db/vacancies")
async def db_vacancies(id=None):
    with Session() as session:
        if id != None:
            return session.query(Vacancy).filter_by(hh_id=id).all()
        return session.query(Vacancy).all()
    
@app.get("/db/init")
async def db_init():
    init_database(db_url)

@app.get("/db/fill")
async def db_fill():
    extractor = HHExtractor(db_url)
    extractor.run_etl()
