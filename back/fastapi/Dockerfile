# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /fastapi

# Copy the requirements file and install dependencies
COPY ./fastapi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./fastapi/app ./app/
COPY ./DB ./DB/
COPY ./services/hh_etl.py ./services/

# Expose the port FastAPI will run on
EXPOSE 80

# Command to run the application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]