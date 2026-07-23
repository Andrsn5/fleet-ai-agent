FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and migration configs
COPY ./app /app/app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Expose port
EXPOSE 8000

# Apply DB migrations and start API
CMD ["/bin/sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
