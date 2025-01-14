# Use an official Python image as a base
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create static directory and set permissions
RUN mkdir -p /app/app/static && chmod -R 755 /app/app/static

# Copy the entire project directory to the container
COPY . .

# Ensure static files have proper permissions
RUN chmod -R 755 /app/app/static

# Expose the port your app runs on
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]