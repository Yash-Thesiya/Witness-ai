FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/app ./app

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "app/main.py"]
