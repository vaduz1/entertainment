FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    minicom \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir streamlit pyserial pandas python-dotenv beautifulsoup4 python-dotenv

COPY app /app

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
