FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-symbola \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "streamlit run streamlit_financial_report_v7_6.py --server.port $PORT --server.address 0.0.0.0"]
