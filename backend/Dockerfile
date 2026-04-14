FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2 and llama-cpp (g++, cmake)
RUN apt-get update \
    && apt-get -y install libpq-dev gcc g++ cmake make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
