FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /persistent

EXPOSE 80

CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0", "--server.headless=true"]
