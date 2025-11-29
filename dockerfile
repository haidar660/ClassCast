# 1. Base image: full Python 3.11 (larger, but easier & faster to work with)
FROM python:3.11

# 2. Workdir inside the container
WORKDIR /app

# 3. Copy only requirements first (for better build caching)
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the project files
COPY . .

# 6. Expose the port FastAPI will run on inside the container
EXPOSE 8000

# 7. Command to start the server
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
