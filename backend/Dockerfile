FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend build from the local frontend_dist directory
COPY frontend_dist /app/frontend_dist/

# Copy the backend application code
COPY ./ /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV MONGODB_URI=${MONGODB_URI}

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 