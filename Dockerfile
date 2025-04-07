FROM python:3.11-slim

WORKDIR /app

# Argomenti opzionali per personalizzare l'ambiente
ARG APP_ENV=production
ARG DB_HOST=localhost
ARG DB_PORT=5432
ARG DB_NAME=funnel_manager
ARG DB_USER=postgres
ARG DB_PASSWORD=postgres

# Imposta le variabili di ambiente
ENV APP_ENV=${APP_ENV} \
    DB_HOST=${DB_HOST} \
    DB_PORT=${DB_PORT} \
    DB_NAME=${DB_NAME} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia il file requirements.txt
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Espone la porta per Streamlit
EXPOSE 8501

# Comando per eseguire l'applicazione
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Healthcheck per verificare che l'applicazione sia in esecuzione
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1