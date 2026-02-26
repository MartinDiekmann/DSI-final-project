# Basierend auf dem offiziellen Python-Image
FROM python:3.11-slim

# Arbeitsverzeichnis im Container setzen
WORKDIR /app
ENV PYTHONPATH=/app

# Kopiere den Anwendungscode in den Container
COPY . /app/

# Abhängigkeit installieren
RUN pip install --no-cache-dir -r requirements.txt 

# Setze Umgebungsvariable
ENV PORT=8501
ENV APP_TITLE=Cancer_RiskFactors
ENV DOCKER_ENV=TRUE 

# Starte die App direkt mit dem Python-Interpreter
CMD ["streamlit", "run", "streamlit_cancer_inzidence.py", "--server.port=8501", "--server.address=0.0.0.0"]
