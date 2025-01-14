FROM python:3.10.13-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && \
    pipenv install --system --deploy

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]