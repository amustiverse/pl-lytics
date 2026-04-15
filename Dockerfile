FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/football.db

EXPOSE 8501

CMD ["python", "main.py"]