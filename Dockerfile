# Use a stable version of Python, like 3.10
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install system-level dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev

# Copy requirements.txt to the container
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files into the container
COPY . /app

# Set environment variable to make Flask output to console
ENV FLASK_ENV=development
ENV FLASK_APP=app.py

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask server
CMD ["flask", "run", "--host=0.0.0.0"]
