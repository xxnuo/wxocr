FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask

COPY wcocr.so /app/wcocr.so

COPY wx /app/wx

COPY main.py /app/main.py
COPY templates /app/templates

WORKDIR /app

CMD ["python", "main.py"]