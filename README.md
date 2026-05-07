# Gestor Legislativo

Sistema integral desarrollado en **Django** para la gestión, seguimiento y organización del trabajo legislativo (Proyectos de Ley, Resoluciones, Declaraciones, etc.) para diputados y sus equipos de asesores.

## 🚀 Características Principales

* **Gestión de Proyectos**: Creación, edición y seguimiento del estado de los proyectos legislativos.
* **Sistema de Actualizaciones (Bitácora)**: Registro detallado de los avances de cada proyecto mediante un editor de texto enriquecido (CKEditor) integrado con carga asíncrona (AJAX).
* **Control de Comisiones (Ruta)**: Seguimiento de los giros a comisiones y los dictámenes obtenidos.
* **Organización en Temarios**: Agrupación de proyectos para tratar en sesiones específicas o reuniones de bloque.
* **Generación de Reportes PDF**: Exportación automatizada de los proyectos y temarios a formato PDF listo para imprimir o compartir.
* **Roles y Permisos**: Accesos diferenciados para el Diputado/a, Asesores y Administradores del sistema.

## 🛠️ Stack Tecnológico

* **Backend**: Python 3.x, Django 5.x
* **Base de Datos**: SQLite (por defecto) / PostgreSQL (recomendado para producción)
* **Frontend**: HTML5, CSS3, Vanilla JS, Bootstrap 5
* **Herramientas de Texto**: CKEditor 4 (vía `django-ckeditor`)
* **Generación de PDF**: ReportLab
* **Despliegue**: Preparado para entornos WSGI (ej: PythonAnywhere, Heroku, VPS)

## ⚙️ Instalación y Configuración Local

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_DIRECTORIO>
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   - Copiar el archivo `.env.example` a `.env` y ajustar los valores (SECRET_KEY, DEBUG, base de datos, etc).

5. **Aplicar migraciones:**
   ```bash
   cd diputada
   python manage.py migrate
   ```

6. **Crear superusuario (Administrador):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Recolectar archivos estáticos (Para producción/pruebas):**
   ```bash
   python manage.py collectstatic
   ```

8. **Ejecutar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

## ☁️ Guía Rápida para Despliegue (PythonAnywhere)

Para desplegar una nueva instancia para otro diputado en PythonAnywhere:

1. Crea una cuenta nueva o inicia sesión en PythonAnywhere.
2. Abre una consola Bash y clona este repositorio: `git clone <URL_DEL_REPOSITORIO>`
3. Crea un entorno virtual (`mkvirtualenv --python=/usr/bin/python3.10 mi_entorno`) e instala el `requirements.txt`.
4. Ve a la pestaña **Web** y crea una nueva **Web App** (elige configuración manual de Django).
5. Configura la ruta del código fuente (Source code) y del entorno virtual (Virtualenv).
6. Edita el archivo de configuración **WSGI** para apuntar al archivo `settings.py` de la aplicación (`diputada.configuraciones.settings`).
7. En la pestaña **Web**, mapea las rutas de archivos estáticos (`/static/` y `/media/`) hacia las carpetas correspondientes en tu proyecto.
8. En la consola, ejecuta `python manage.py migrate`, `python manage.py createsuperuser` y `python manage.py collectstatic`.
9. ¡Recarga la Web App y listo!

## 📝 Licencia
Propiedad Privada. Todos los derechos reservados.
