FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app/app
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

EXPOSE 8000

CMD ["/bin/bash", "/app/run.sh"]
