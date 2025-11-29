# 1. Base image: full Python 3.11 (includes needed libs)
FROM python:3.11

# 2. Workdir inside container
WORKDIR /app

# 3. Copy requirements first (for caching optimization)
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project files
COPY . .

# 6. Expose FastAPI port
EXPOSE 8000

# 7. Start the FastAPI server
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
