FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gettext \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

WORKDIR /app

COPY ./requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app/staticfiles
RUN chown -R appuser:appuser /app/logs
RUN chown -R appuser:appuser /app/locale

RUN chmod +x scripts/entrypoint.sh

USER appuser

ENTRYPOINT ["scripts/entrypoint.sh"]