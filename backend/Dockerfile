# Use Docker image with Python version 3
FROM python:3.7.3

# Print messages immediately instead of using a buffer
ENV PYTHONUNBUFFERED 1

# Install dependencies or use Docker cache
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# Copy Python code into Docker
ADD tc2 tc2
ADD webpanel webpanel
ADD manage.py /manage.py
ADD config.properties config.properties
RUN mkdir /sessions

# Populate the sql database with django models and settings
CMD ["python", "manage.py", "migrate", "auth"]
CMD ["python", "manage.py", "createadminuser"]
# Detect any django changes that need to alter the sql database structure
CMD ["python", "manage.py", "makemigrations"]
# Apply migrations to update the sql database schema
CMD ["python", "manage.py", "migrate", "--fake-initial"]
CMD ["python", "manage.py", "migrate"]
CMD ["python", "manage.py", "createadminuser"]

# Start the application server (gunicorn). This also calls a runtime hook to start collecting data and trading
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "webpanel.wsgi:application", "--timeout", "90"]