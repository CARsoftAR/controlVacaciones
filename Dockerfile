# Usar una imagen base oficial de Python ligera
FROM python:3.10-slim

# Establecer variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    libpq-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Cambiar al directorio donde está manage.py
WORKDIR /app/controlDeVacaciones

# Exponer el puerto donde corre la app (solo informativo)
EXPOSE 8000

# Comando para correr la aplicación usando Gunicorn
CMD ["gunicorn", "controlDeVacaciones.wsgi:application", "--bind", "0.0.0.0:8000"]
