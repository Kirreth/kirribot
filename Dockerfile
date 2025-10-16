# Python-Image verwenden
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Anforderungen kopieren
COPY requirements.txt .

# Pakete installieren
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

# Startkommando (optional, weil schon in docker-compose angegeben)
CMD ["python", "main.py"]
