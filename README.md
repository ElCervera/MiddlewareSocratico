# 🎓 Middleware Socrático - Tutor de Programación con IA

Tutor de programación basado en inteligencia artificial que utiliza el **método socrático** para guiar a los estudiantes a través de preguntas reflexivas, en lugar de entregar código resuelto. Desarrollado con Python, LangChain, Gemini (Google) y Chainlit.

## 🎯 Objetivo del Proyecto

El Middleware Socrático es una herramienta educativa diseñada para fomentar el aprendizaje profundo de la programación. En lugar de dar respuestas directas, el tutor hace preguntas que ayudan al estudiante a:

- Descomponer problemas complejos en pasos sencillos
- Descubrir errores por sí mismo
- Desarrollar pensamiento crítico y metacognición
- Construir soluciones de forma autónoma

## ✨ Características Principales

- **Interfaz web moderna y responsive con Chainlit
- Integración con el modelo Gemini 1.5 Flash de Google
- Filtros automáticos para bloquear código en respuestas
- Validación de respuestas socráticas (debe contener preguntas)
- Historial de conversación por sesión
- Sistema de reintentos (hasta 2 intentos) y respaldo con preguntas genéricas
- Listo para desplegar en Render (plan gratuito)

## 📋 Requisitos Previos

- **Python 3.8+ instalado
- **Clave API de Google Gemini** (obténla en [Google AI Studio](https://aistudio.google.com/))
- **Git** (para control de versiones y despliegue)
- **Cuenta en GitHub** (para despliegue en Render)
- **Cuenta en Render** (plan gratuito disponible)

## 🚀 Ejecución Local

Sigue estos pasos para ejecutar el proyecto en tu máquina local:

### 1. Clonar o crear el proyecto

```bash
mkdir middleware-socratico
cd middleware-socratico
```

### 2. Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env` y reemplaza `TU_API_KEY_AQUI` por tu clave API real:

```env
GOOGLE_API_KEY=tu_api_key_de_google_gemini_aqui
```

### 5. Ejecutar la aplicación

```bash
chainlit run app.py -w
```

El parámetro `-w` activa el modo watch para recargar automáticamente al detectar cambios en el código.

La aplicación estará disponible en: **http://localhost:8000**

## ☁️ Despliegue en Render (Plan Gratuito)

### Paso 1: Preparar el repositorio en GitHub

1. Crea un nuevo repositorio en GitHub (público o privado)
2. Sube todos los archivos del proyecto al repositorio:

```bash
git init
git add .
git commit -m "Middleware Socrático inicial"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

> **Importante:** No subas el archivo `.env` a GitHub (ya está en `.gitignore`). La clave API se configurará directamente en Render.

### Paso 2: Conectar Render con GitHub

1. Ve a [render.com](https://render.com) y crea una cuenta o inicia sesión
2. Haz clic en **"New +"** → **"Web Service"**
3. Conecta tu cuenta de GitHub y selecciona el repositorio del proyecto
4. Configura el servicio con los siguientes parámetros:

| Campo | Valor |
|-------|-------|
| **Name** | El nombre que quieras darle a tu servicio |
| **Region** | Selecciona la más cercana a ti |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `chainlit run app.py --host 0.0.0.0 --port $PORT` |

### Paso 3: Configurar variables de entorno

En la sección **"Advanced"** → **"Environment Variables"**:

1. Agrega una nueva variable:
   - **Key:** `GOOGLE_API_KEY`
   - **Value:** Tu clave API de Google Gemini

### Paso 4: Desplegar

1. Haz clic en **"Create Web Service"**
2. Espera a que Render termine de construir y desplegar la aplicación (toma 2-5 minutos)
3. Cuando el estado sea **"Live"**, haz clic en la URL proporcionada por Render para acceder a tu tutor

## 📁 Estructura del Proyecto

```
middleware-socratico/
├── .env                     # Variables de entorno (clave API)
├── .gitignore               # Archivos a ignorar en Git
├── app.py                   # Archivo principal de la aplicación
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación del proyecto
└── utils/
    └── filters.py           # Funciones para filtrar respuestas (bloquear código)
```

## 🎯 Reglas de Comportamiento

El sistema sigue estrictamente estas reglas:

- ✅ **NUNCA** entrega código completo o funcional
- ✅ Siempre responde con preguntas que guíen al estudiante
- ✅ Descompone problemas complejos en subproblemas
- ✅ Fomenta la metacognición y el pensamiento crítico
- ✅ Filtra automáticamente cualquier bloque de código en las respuestas
- ✅ Si detecta código, pide a la IA que reformule (hasta 2 intentos)
- ✅ Después de 2 intentos fallidos, muestra preguntas guía genéricas

## 💡 Tips para el Estudiante

1. Sé específico con tus preguntas
2. Comparte tu proceso de pensamiento, no solo pides respuestas
3. Si te atascas, explica qué has intentado hasta ahora
4. Responde a las preguntas del tutor: ¡te acercan a la solución!
5. No tengas miedo a equivocarte: los errores son parte del aprendizaje

## 🔧 Tecnologías Utilizadas

- **Python 3.8+**: Lenguaje de programación
- **LangChain 0.3.0**: Orquestación de cadenas de IA
- **Google Gemini 1.5 Flash**: Modelo de lenguaje
- **langchain-google-genai 1.0.0**: Integración LangChain ↔ Gemini
- **Chainlit 1.0.0**: Interfaz web de chat
- **python-dotenv 1.0.0**: Gestión de variables de entorno
- **Render**: Plataforma de despliegue en la nube

## ❓ Preguntas Frecuentes (FAQ)

**¿Por qué no me da el código directamente?
> Porque el objetivo es que aprendas a programar, no que copies soluciones. El método socrático te ayuda a desarrollar habilidades de resolución de problemas que durarán toda la vida.

**¿Qué lenguajes de programación soporta?
> Principalmente Python, pero puedes preguntar por conceptos generales de programación, algoritmos y estructuras de datos.

**¿Puedo usar otro modelo de IA?
> Sí, solo modifica la inicialización del modelo en `app.py`. Actualmente está configurado para Gemini, pero LangChain soporta muchos otros proveedores.

**¿El plan gratuito de Render es suficiente?
> Sí, para uso personal y pruebas. El plan gratuito tiene límites de uso, pero es ideal para proyectos pequeños y educación.

**¿Cómo puedo personalizar el comportamiento del tutor?
> Edita el `PROMPT_SOCRATICO` en `app.py` para ajustar el tono, estilo o añadir reglas específicas.

## 📝 Licencia

Este proyecto está diseñado para fines educativos. ¡Siéntete libre de usarlo, modificarlo y aprender con él!
