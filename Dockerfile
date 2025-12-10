# official Python runtime as a parent image
FROM python:3.11-slim

# working directory
WORKDIR /app

# current directory contents into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the web server (Gunicorn)
# The $PORT environment variable is set automatically by Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app