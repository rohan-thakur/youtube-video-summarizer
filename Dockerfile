FROM python:3.9-slim

# Set environment variable for PORT
ENV PORT 8080

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Set Streamlit to run on specified port and address
CMD ["streamlit", "run", "streamlit_app.py", "--server.enableCORS", "false", "--browser.serverAddress", "0.0.0.0", "--browser.gatherUsageStats", "false", "--server.port", "8080"]