# Guia para Mover el Proyecto a Otra Computadora

Esta guía detalla los pasos para transferir tu entorno de desarrollo del "Sistema de Control de Vacaciones" a una nueva computadora.

## 1. En la Computadora Actual (Origen)

Lo primero es asegurar que todo tu código esté guardado en la nube (GitHub).

1.  **Abre una terminal** en la carpeta de tu proyecto.
2.  **Verifica el estado**:
    ```powershell
    git status
    ```
3.  **Guarda los cambios** (si hay archivos pendientes):
    ```powershell
    git add .
    git commit -m "Guardando todo para migrar de PC"
    ```
4.  **Sube el código a GitHub**:
    ```powershell
    git push origin main
    ```
    *(Nota: Si usas otra rama en lugar de `main`, usa el nombre correcto).*

### ¿Necesitas mover los datos (Base de Datos)?
Git **NO** guarda tu base de datos (ya que está en el archivo `.gitignore` o dentro de un volumen de Docker).
*   **Si NO te importan los datos de prueba**: Puedes saltar este paso. En la nueva PC empezarás con una base de datos limpia.
*   **Si SI necesitas los datos**: Necesitas hacer un respaldo.
    *   *Si usas Docker*:
        ```powershell
        docker compose exec db mysqldump -u root -prootpassword vacacionesAbbamat > respaldo_datos.sql
        ```
    *   Sube este archivo `respaldo_datos.sql` a Google Drive, envíatelo por correo, o ponlo en el repo temporalmente (luego bórralo por seguridad).

---

## 2. En la Nueva Computadora (Destino)

### A. Preparación Previa
Instala las herramientas necesarias:
1.  **Git**: [Descagar Git](https://git-scm.com/downloads)
2.  **Docker Desktop** (Recomendado): [Descargar Docker](https://www.docker.com/products/docker-desktop/)
    *   *Alternativa sin Docker*: Instala Python 3.10+ y MySQL Server manualmente.

### B. Descargar el Proyecto
1.  Crea una carpeta donde guardarás tus proyectos (ej: `C:\Proyectos`).
2.  Abre la terminal en esa carpeta.
3.  Clona tu repositorio:
    ```powershell
    git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
    cd ControlDeVacaciones
    ```

### C. Levantar el Proyecto (Opción Docker - Más Fácil)
Como ya tienes `docker-compose.yml`, esta es la forma más rápida.

1.  En la terminal dentro de la carpeta del proyecto:
    ```powershell
    docker compose up --build
    ```
2.  Espera a que termine de construir.
3.  Abre `http://localhost:8000` en tu navegador.
    *   *Nota*: La primera vez, la base de datos estará vacía.

### D. Restaurar Datos (Opcional)
Si hiciste el respaldo `respaldo_datos.sql` en el paso 1:
1.  Asegúrate que el proyecto esté corriendo (`docker compose up`).
2.  Abre otra terminal y ejecuta:
    ```powershell
    docker compose exec -T db mysql -u root -prootpassword vacacionesAbbamat < respaldo_datos.sql
    ```

---

## 3. Levantar el Proyecto (Opción Manual / Sin Docker)
Si prefieres no usar Docker en la nueva PC:

1.  **Instala Python**.
2.  **Crea el entorno virtual**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Instala librerías**:
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Configura la Base de Datos**:
    *   Asegúrate de tener un servidor MySQL corriendo.
    *   Crea una base de datos llamada `vacacionesAbbamat`.
    *   Modifica (o crea) un archivo `.env` con las credenciales de tu MySQL local.
5.  **Ejecuta las migraciones**:
    ```powershell
    python manage.py migrate
    ```
6.  **Corre el servidor**:
    ```powershell
    python manage.py runserver
    ```
