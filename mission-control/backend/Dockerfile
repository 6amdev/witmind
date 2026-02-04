FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app

# Expose port
EXPOSE 4000

# Run
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "4000"]
