FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential ffmpeg libgl1 libglib2.0-0 git         && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
EXPOSE 5000
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "app:app", "-b", "0.0.0.0:5000"]
