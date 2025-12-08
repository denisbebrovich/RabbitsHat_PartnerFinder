from fastapi import FastAPI
from api.data_api import router as data_router
from api.ml_api import router as ml_router

app = FastAPI(
    title="Partner Finder API",
    description="API для поиска компаний-партнеров",
    version="1.0.0"
)

app.include_router(data_router)
app.include_router(ml_router)

@app.get("/")
async def root():
    return {"message": "Partner Finder API работает!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "partner-finder-api"}