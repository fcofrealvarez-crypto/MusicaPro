FROM python:3.11-slim

# Instalar FFmpeg (Requisito fundamental para yt-dlp y procesamiento de audio)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias primero (para aprovechar el caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto
EXPOSE 10000

# Iniciar FastAPI en el puerto 10000 (Render requiere el host 0.0.0.0)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
