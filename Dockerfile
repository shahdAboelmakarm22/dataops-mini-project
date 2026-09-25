# 1. Start from a Python base image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 2. Copy requirements.txt first (better layer caching)
COPY requirements.txt .

# 3. Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the project files
COPY . .

# 5. Run the Python data pipeline
CMD ["python", "src/transform.py"]
