FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install OOS SDK if provided in sdk/ directory
COPY sdk/ /tmp/sdk/
RUN if [ -f /tmp/sdk/requirements.txt ]; then \
      pip install --no-cache-dir -r /tmp/sdk/requirements.txt && \
      if [ -f /tmp/sdk/install_extension.sh ]; then sh /tmp/sdk/install_extension.sh; fi; \
    fi

COPY src/ ./src/
COPY sql/ ./sql/

RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
