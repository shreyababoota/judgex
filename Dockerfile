FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
        g++ \
        time \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["gunicorn", "run:app"]