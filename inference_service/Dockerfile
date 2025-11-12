FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY app/ ./app
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]