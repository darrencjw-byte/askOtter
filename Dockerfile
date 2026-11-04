# Streamlit Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py rag_engine.py google_auth.py drive_sync.py cookie_auth.py .
COPY .streamlit .streamlit/

# Expose Streamlit default port (but we'll run on 3000)
EXPOSE 3000

# Set environment variables
ENV STREAMLIT_SERVER_PORT=3000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=3000", "--server.address=0.0.0.0"]
