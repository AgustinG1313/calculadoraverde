# BioTrack - Aplicación de Sostenibilidad Energética

Este proyecto consiste en una aplicación web para el seguimiento del consumo energético personal, construida con FastAPI para el backend y Streamlit para el frontend.

## Estructura del Proyecto

El proyecto está dividido en dos componentes principales: `backend` y `frontend`.

- **`backend/`**: Contiene la API de FastAPI.
  - `app/main.py`: Punto de entrada de la API.
  - `app/routers/`: Módulos con los endpoints agrupados por funcionalidad.
  - `app/schemas.py`: Modelos de datos de Pydantic.
  - `app/utils.py`: Lógica de negocio y cálculos.
  - `app/database.py`: Simulación de la base de datos.

- **`frontend/`**: Contiene la aplicación de Streamlit.
  - `app.py`: Punto de entrada de la interfaz de usuario.
  - `pages/`: Módulos para cada página de la aplicación.
  - `components/`: Componentes reutilizables de la interfaz.
  - `services/`: Cliente para consumir la API del backend.
  - `assets/`: Archivos estáticos como CSS.

## Cómo Ejecutar el Proyecto

### Prerrequisitos

- Python 3.9 o superior.
- pip (gestor de paquetes de Python).

### Instalación

1.  **Clona el repositorio (o descomprime los archivos) y navega a la carpeta raíz `biotrack/`.**

2.  **Instala las dependencias:**
    Se recomienda crear un entorno virtual.
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
    Luego, instala los paquetes desde el archivo `requirements.txt`:
    ```bash
    pip install -r frontend/requirements.txt
    ```

### Ejecución

Necesitarás dos terminales para ejecutar el backend y el frontend simultáneamente.

1.  **Terminal 1: Iniciar el Backend (FastAPI)**

    Navega a la carpeta `backend` y ejecuta Uvicorn:
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    El servidor de la API estará disponible en `http://127.0.0.1:8000`.

2.  **Terminal 2: Iniciar el Frontend (Streamlit)**

    Navega a la carpeta raíz del proyecto (`biotrack/`) y ejecuta Streamlit:
    ```bash
    streamlit run frontend/app.py
    ```
    La aplicación web se abrirá en tu navegador, generalmente en `http://localhost:8501`.

¡Y listo! Ahora puedes interactuar con la aplicación BioTrack.