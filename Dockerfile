FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY mqtt_to_db.py .
COPY web_app.py .
COPY templates/ templates/

CMD ["python", "mqtt_to_db.py"]
