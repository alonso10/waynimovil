# Importador de Datos TXT a MongoDB (SOLID)

Este proyecto proporciona una herramienta para importar datos desde archivos de texto plano (TXT) con un formato específico hacia una base de datos MongoDB. La solución está diseñada siguiendo los principios SOLID para facilitar su mantenimiento, testabilidad y reutilización, ofreciendo tanto una Interfaz de Línea de Comandos (CLI) como una API web (construida con FastAPI).

## Descripción

La aplicación lee archivos TXT que contienen información sobre deudores y entidades financieras, procesa estos datos para calcular valores agregados (como la situación más desfavorable y la suma de préstamos por deudor, y la suma total de préstamos por entidad), y finalmente guarda los resultados en colecciones separadas dentro de una base de datos MongoDB.

## Prerrequisitos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

* **Python:** Versión 3.8 o superior.
* **MongoDB:** Una instancia de MongoDB en ejecución (local o remota).
* **pip:** El gestor de paquetes de Python (normalmente viene con Python).

## Configuración del Proyecto

Sigue estos pasos para configurar el entorno de desarrollo:

1.  **Clonar el Repositorio (Opcional):**
    Si aún no tienes el código, clona el repositorio:
    ```bash
    git clone <url-del-repositorio>
    cd <nombre-del-directorio>
    ```

2.  **Crear un Entorno Virtual:**
    Es altamente recomendable usar un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    # Crear el entorno virtual (puedes llamarlo 'venv' o como prefieras)
    python -m venv venv
    # Activar el entorno virtual
    # En macOS/Linux:
    source venv/bin/activate
    # En Windows (cmd):
    .\venv\Scripts\activate
    # En Windows (PowerShell):
    .\venv\Scripts\Activate.ps1
    ```

3.  **Instalar Dependencias:**
    Instala todas las librerías necesarias listadas en el archivo `requirements.txt` (si no lo tienes, crea uno con el contenido de abajo o instálalas manualmente).
    ```bash
    pip install -r requirements.txt
    ```
    *Contenido mínimo para `requirements.txt`:*
    ```txt
    typer[all]>=0.9.0,<1.0.0
    fastapi>=0.100.0,<1.0.0
    uvicorn[standard]>=0.20.0,<1.0.0
    motor>=3.0.0,<4.0.0
    aiofiles>=22.1.0,<24.0.0
    pydantic>=2.0.0,<3.0.0
    python-dotenv>=1.0.0,<2.0.0
    # rich (para Typer y mejor formato) es instalado por typer[all]
    ```

4.  **Configurar Variables de Entorno:**
    Crea un archivo llamado `.env` en la raíz del proyecto y define las siguientes variables. Ajusta los valores según tu configuración:

    ```dotenv
    # .env
    MONGO_CONNECTION_STRING="mongodb://localhost:27017/" # Cambia si tu MongoDB está en otro lugar o requiere autenticación
    DB_NAME="solid_importer_db"                         # Nombre de la base de datos a usar
    DEBTORS_COLLECTION="debtors"                        # Nombre de la colección para deudores
    ENTITIES_COLLECTION="entities"                      # Nombre de la colección para entidades

    # Opcional: Puedes definir aquí las rutas por defecto si es necesario,
    # aunque generalmente se pasan como argumentos o se configuran de otra forma.
    # INPUT_TXT_FILE="datos_default.txt"
    ```
    La aplicación cargará estas variables automáticamente al iniciarse.

## Ejecución

Puedes ejecutar la aplicación de dos maneras:

### 1. Usando la Interfaz de Línea de Comandos (CLI)

La CLI es útil para procesar archivos individuales manualmente.

* **Comando Básico:**
    ```bash
    python cli.py import-file /ruta/completa/a/tu/archivo.txt
    ```
    Reemplaza `/ruta/completa/a/tu/archivo.txt` con la ruta real de tu archivo de datos TXT.

* **Ayuda:**
    Para ver todas las opciones y comandos disponibles:
    ```bash
    python cli.py --help
    ```
    Para obtener ayuda sobre un comando específico:
    ```bash
    python cli.py import-file --help
    ```

### 2. Usando la API Web (FastAPI)

La API permite integrar la funcionalidad de importación en otras aplicaciones o servicios.

* **Iniciar el Servidor:**
    Desde la raíz del proyecto, ejecuta el siguiente comando para iniciar el servidor web Uvicorn:
    ```bash
    uvicorn waynimovil.api.main:app --reload --host 0.0.0.0 --port 8000
    ```
    * `waynimovil.api.main:app`: Indica la ubicación de la instancia de FastAPI (`app` dentro de `main.py` en el paquete `api` del módulo `waynimovil`). Asegúrate de que esta ruta coincida con tu estructura de directorios. Si tu script `main.py` está directamente en `api/`, podría ser `api.main:app`. Ajusta según sea necesario.
    * `--reload`: Reinicia el servidor automáticamente cuando detecta cambios en el código (útil para desarrollo).
    * `--host 0.0.0.0`: Hace que la API sea accesible desde otras máquinas en la red (si es necesario). Usa `127.0.0.1` para acceso local únicamente.
    * `--port 8000`: Especifica el puerto en el que se ejecutará la API.

* **Acceder a la Documentación Interactiva:**
    Una vez que el servidor esté en ejecución, abre tu navegador web y ve a:
    `http://127.0.0.1:8000/docs`
    Aquí encontrarás la documentación interactiva (Swagger UI) donde puedes probar el endpoint de la API directamente desde el navegador.

* **Usar el Endpoint de Importación:**
    El endpoint principal es `POST /v1/import-txt-file/`. Debes enviar una solicitud `POST` con el archivo TXT adjunto como `multipart/form-data`.

    * **Ejemplo con `curl`:**
        ```bash
        curl -X POST "[http://127.0.0.1:8000/v1/import-txt-file/](http://127.0.0.1:8000/v1/import-txt-file/)" \
             -H "accept: application/json" \
             -H "Content-Type: multipart/form-data" \
             -F "file=@/ruta/completa/a/tu/archivo.txt;type=text/plain"
        ```
        Reemplaza `/ruta/completa/a/tu/archivo.txt` con la ruta real de tu archivo.

## Estructura del Proyecto (Resumen)
```bash
    waynimovil/
      ├── core/             # Lógica central (modelos, parser, procesador, repositorio, config)
      ├── api/              # Código de la API FastAPI (main.py, routers, dependencies)
      ├── cli.py            # Código de la Interfaz de Línea de Comandos (Typer)
      ├── .env              # Archivo de variables de entorno (NO incluir en Git si tiene secretos)
      ├── requirements.txt  # Dependencias de Python
      └── README.md         # Este archivo
```

## Configuración Adicional

Revisa el archivo `core/config.py` si necesitas ajustar las constantes de parseo (slices) para el formato del archivo TXT. Las variables de conexión a la base de datos se gestionan a través del archivo `.env`.
