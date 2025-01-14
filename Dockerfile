FROM python:3.10.13-slim

WORKDIR /app

# Copy Pipfile and lock files, then install dependencies
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy the application code
COPY . .

# Explicitly expose the port
EXPOSE 8000

# Use the correct syntax for environment variable substitution
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]


# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]