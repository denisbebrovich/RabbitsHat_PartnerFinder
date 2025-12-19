FROM python:3.9-slim-buster

WORKDIR /app

COPY fastapi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY DB ./DB
COPY services ./services
COPY scripts ./scripts

COPY fastapi/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]