import os
import re
import logging
from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Select
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from utils.filters import contiene_codigo, limpiar_respuesta
from config.model_factory import (
    get_llm,
    get_nombre_modelo,
    MODELOS_DISPONIBLES,
    MODELO_POR_DEFECTO,
)

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Advertencia si no hay GOOGLE_API_KEY (necesaria para fallback y modelos Google)
if not os.getenv("GOOGLE_API_KEY"):
    logger.warning(
        "No se encontró GOOGLE_API_KEY. Los modelos de Google y el fallback "
        "no estarán disponibles. Solo funcionarán modelos gratuitos de OpenCode Zen."
    )

# ============================================================================
# PROMPT SOCRÁTICO - System Prompt
# ============================================================================
PROMPT_SOCRATICO = """Eres un tutor socrático especializado en programación e ingeniería de software. Tu misión es guiar a los estudiantes para que descubran las soluciones por sí mismos, PERO también proporcionas explicaciones claras y concisas cuando el estudiante está aprendiendo un concepto nuevo.

## REGLAS DE COMPORTAMIENTO:

### 1. SI ES UN CONCEPTO NUEVO O BÁSICO (para principiantes):
   - **Primero, da una explicación breve y clara** (máximo 3-4 oraciones) del concepto en cuestión.
   - **Luego, haz preguntas** para que el estudiante aplique lo que acaba de aprender.
   - Ejemplo: "Las variables booleanas son aquellas que solo pueden tener dos valores: True o False. Se usan para representar condiciones que se cumplen o no, como 'la puerta está abierta' o 'el usuario tiene permiso'. Ahora, ¿puedes pensar en una situación cotidiana donde uses una decisión de sí/no?"

### 2. SI ES UN PROBLEMA DE PROGRAMACIÓN O DISEÑO (avanzado):
   - **No des código**, pero puedes dar pistas conceptuales y preguntas guía.
   - Ejemplo: "Para ordenar una lista, piensa en cómo compararías dos elementos... ¿qué pasos harías manualmente?"

### 3. NUNCA, bajo ninguna circunstancia, entregues código completo o funcional.
   - No escribas bloques de código con ```
   - No escribas funciones, clases, bucles, condicionales ni estructura de código.

### 4. SI EL ESTUDIANTE INSISTE EN CÓDIGO:
   - Responde con: "Entiendo que quieras el código, pero mi función es ayudarte a aprender. Vamos a construir la lógica paso a paso. Dime, ¿cómo empezarías a resolver este problema?"

### 5. ADAPTA TU TONO AL NIVEL DEL ESTUDIANTE:
   - Si el estudiante parece principiante (preguntas básicas), da explicaciones más detalladas y preguntas más simples.
   - Si el estudiante muestra conocimiento avanzado, haz preguntas más profundas (diseño, optimización, testing).

## EJEMPLOS DE INTERACCIÓN CORRECTA:

**Principiante:**
Estudiante: "¿Qué son las variables booleanas?"
Tú: "Las variables booleanas son un tipo de dato que solo puede tener dos valores: True (verdadero) o False (falso). Se usan para representar condiciones, como 'el usuario está logueado' o 'el número es par'. Ahora, piensa en una situación cotidiana donde tomes una decisión basada en una condición de sí/no. ¿Cómo la expresarías con una variable booleana?"

**Avanzado:**
Estudiante: "¿Cómo diseño una clase para un sistema de autenticación?"
Tú: "Excelente pregunta de diseño. Para empezar, ¿qué responsabilidades debería tener una clase que maneje autenticación? ¿Qué métodos necesitaría? ¿Cómo separarías la lógica de verificación de credenciales de la lógica de sesión?"

## EJEMPLOS DE INTERACCIÓN INCORRECTA (PROHIBIDA):
❌ "Aquí tienes el código: def autenticar(usuario, pass): return pass == '1234'"
❌ "Lo que debes hacer es usar un for loop con range(10)"
❌ "Las variables booleanas son True o False." (sin preguntas de seguimiento)

## RECUERDA SIEMPRE:
Tu objetivo es que el estudiante aprenda a PENSAR COMO INGENIERO/A, no que copie código. Pero para lograrlo, a veces necesitas darle las herramientas conceptuales básicas antes de guiarlo con preguntas.
"""

# ============================================================================
# Configuración del modelo y cadenas
# ============================================================================

# Inicializar el LLM usando la fábrica de modelos (lee ACTIVE_MODEL del .env)
# Con fallback automático a Gemini directo si el proxy OpenCode no está disponible
llm = get_llm(temperature=0.3)

# Crear el prompt template con historial de conversación
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", PROMPT_SOCRATICO),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)

# Crear la cadena base (prompt | llm)
chain = prompt_template | llm

# Diccionario para almacenar historiales de conversación por sesión
historiales = {}


def obtener_historial(session_id: str) -> ChatMessageHistory:
    """
    Obtiene o crea el historial de mensajes para una sesión.

    Args:
        session_id: Identificador único de la sesión.

    Returns:
        Objeto ChatMessageHistory con el historial de la sesión.
    """
    if session_id not in historiales:
        historiales[session_id] = ChatMessageHistory()
    return historiales[session_id]


# Crear la cadena con historial de mensajes
cadena_con_historial = RunnableWithMessageHistory(
    chain,
    get_session_history=obtener_historial,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# ============================================================================
# Funciones auxiliares
# ============================================================================


def validar_respuesta(respuesta: str) -> tuple[bool, str]:
    """
    Valida que la respuesta de la IA cumpla con las reglas del método socrático:
    - No debe contener código
    - Debe contener al menos una pregunta

    Args:
        respuesta: El texto de respuesta de la IA.

    Returns:
        Tupla con (es_valida, mensaje_error o "")
    """
    # Verificar que no contenga código
    if contiene_codigo(respuesta):
        return False, (
            "La respuesta contiene código. Por favor, reformula usando solo preguntas "
            "guía sin escribir código."
        )

    # Verificar que contenga al menos una pregunta (signo de interrogación)
    if "?" not in respuesta:
        return False, (
            "La respuesta debe contener al menos una pregunta para guiar al "
            "al estudiante. Por favor, reformula con preguntas socráticas."
        )

    return True, ""


RESPUESTA_RESPALDO = (
    "¡Vamos a aplicar pensamiento de ingeniería a este problema! Para ayudarte a "
    "encontrar la solución por ti mismo, déjame hacerte algunas preguntas que te "
    "guiarán paso a paso:\n\n"
    "1. **Objetivo y requisitos**: ¿Qué es exactamente lo que quieres lograr? "
    "¿Qué comportamiento correcto debería tener la solución, y qué entradas/salidas "
    "esperas?\n\n"
    "2. **Descomposición del problema**: ¿Cómo dividirías este problema en partes "
    "más pequeñas y atacables? ¿Cuál es el primer subproblema en el que te enfocarías?\n\n"
    "3. **Proceso actual y aprendizaje**: ¿Qué estrategias has intentado hasta ahora? "
    "¿Qué funcionó, qué no funcionó, y qué conclusión sacaste de esos intentos?\n\n"
    "4. **Diseño y calidad**: Si lo piensas como ingeniero/a, ¿qué decisiones de "
    "diseño crees que afectarán la mantenibilidad, legibilidad o posibilidad de testear "
    "esta solución a futuro?\n\n"
    "Respóndeme a estas preguntas y con gusto seguiremos avanzando juntos, con "
    "el foco en que descubras la respuesta razonando como ingeniero/a de software.")


# ============================================================================
# Handlers de Chainlit
# ============================================================================


@cl.on_chat_start
async def on_chat_start():
    """
    Manejador que se ejecuta cuando un usuario inicia una nueva conversación.
    Muestra un mensaje de bienvenida, configura el selector de modelos
    y almacena el modelo activo en la sesión.
    """
    # --- Selector de modelos (dropdown) ---
    modelo_inicial = os.getenv("ACTIVE_MODEL", MODELO_POR_DEFECTO)
    opciones_modelos = list(MODELOS_DISPONIBLES.keys())

    # Determinar el índice inicial del modelo activo
    try:
        indice_inicial = opciones_modelos.index(modelo_inicial)
    except ValueError:
        indice_inicial = 0

    settings = await cl.ChatSettings(
        [
            Select(
                id="modelo_activo",
                label="🤖 Modelo LLM",
                values=opciones_modelos,
                initial_index=indice_inicial,
                description="Selecciona el modelo de IA para tu sesión.",
            ),
        ]
    ).send()

    # Guardar el modelo activo en la sesión del usuario
    modelo_seleccionado = settings.get("modelo_activo", modelo_inicial)
    cl.user_session.set("modelo_activo", modelo_seleccionado)

    # Crear el LLM y la cadena para esta sesión
    llm_sesion = get_llm(model_id=modelo_seleccionado, temperature=0.3)
    chain_sesion = prompt_template | llm_sesion
    cadena_sesion = RunnableWithMessageHistory(
        chain_sesion,
        get_session_history=obtener_historial,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    cl.user_session.set("cadena", cadena_sesion)

    nombre_modelo = get_nombre_modelo(modelo_seleccionado)

    mensaje_bienvenida = (
        "# 🎓 **¡Bienvenido al Tutor Socrático de Programación e Ingeniería de Software!** 🧠\n\n"
        "Soy tu tutor virtual y te ayudaré a **aprender a pensar como ingeniero/a de software**, "
        "usando el método socrático.\n\n"
        f"**Modelo activo:** {nombre_modelo}\n\n"
        "> 💡 *Puedes cambiar el modelo en cualquier momento usando el ícono de "
        "configuración (⚙️) en la barra del chat.*\n\n"
        "## 🎯 Foco de nuestras sesiones:\n\n"
        "Podemos profundizar en:\n"
        "- Lógica, algoritmos y estructuras de datos\n"
        "- Programación orientada a objetos, SOLID y patrones de diseño\n"
        "- Testing, debugging y calidad del código\n"
        "- Arquitectura, diseño de sistemas y bases de datos\n"
        "- Git, flujos de trabajo, despliegue y refactorización\n\n"
        "## 📚 Cómo funcionamos juntos:\n\n"
        "- **Nunca te daré código resuelto** — ¡copiar no te ayuda a pensar como ingeniero.\n"
        "- **Te haré preguntas** para guiar tu razonamiento y que descubras la solución.\n"
        "- Descompondremos problemas complejos en datos → algoritmo → diseño → calidad.\n"
        "- Fomentaremos tu pensamiento crítico y la metacognición sobre tu propio proceso.\n\n"
        "## 🚀 ¿Listo/a para empezar?\n\n"
        "¡Hazme cualquier pregunta! Por ejemplo:\n"
        "- \"¿Cómo debo diseñar esta clase para que sea mantenible?\"\n"
        "- \"Mi algoritmo es lento, ¿por dónde empiezo a optimizar?\"\n"
        "- \"No sé si usar herencia o composición aquí\"\n"
        "- \"¿Cómo planear las pruebas de esta función?\"")

    await cl.Message(
        content=mensaje_bienvenida,
        author="Tutor Socrático",
    ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """
    Manejador que se ejecuta cuando el usuario cambia la configuración
    (selector de modelo) durante una sesión activa.
    """
    nuevo_modelo = settings.get("modelo_activo")
    modelo_anterior = cl.user_session.get("modelo_activo", MODELO_POR_DEFECTO)

    if nuevo_modelo and nuevo_modelo != modelo_anterior:
        # Actualizar el modelo en la sesión
        cl.user_session.set("modelo_activo", nuevo_modelo)

        # Crear nuevo LLM y cadena
        llm_nuevo = get_llm(model_id=nuevo_modelo, temperature=0.3)
        chain_nueva = prompt_template | llm_nuevo
        cadena_nueva = RunnableWithMessageHistory(
            chain_nueva,
            get_session_history=obtener_historial,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        cl.user_session.set("cadena", cadena_nueva)

        nombre_anterior = get_nombre_modelo(modelo_anterior)
        nombre_nuevo = get_nombre_modelo(nuevo_modelo)

        await cl.Message(
            content=(
                f"🔄 **Modelo cambiado exitosamente**\n\n"
                f"- Anterior: {nombre_anterior}\n"
                f"- Nuevo: {nombre_nuevo}\n\n"
                f"El historial de conversación se mantiene. "
                f"Puedes seguir preguntando normalmente."
            ),
            author="Sistema",
        ).send()

        logger.info(
            "Modelo cambiado: %s -> %s (sesión: %s)",
            modelo_anterior,
            nuevo_modelo,
            cl.user_session.get("id"),
        )


@cl.on_message
async def on_message(message: cl.Message):
    """
    Manejador que se ejecuta cuando el usuario envía un mensaje.
    Procesa la consulta, genera una respuesta socrática y la valida.
    Usa la cadena almacenada en la sesión (que puede haber sido cambiada
    por el selector de modelos).
    """
    session_id = cl.user_session.get("id")

    # Obtener la cadena de la sesión (configurada con el modelo seleccionado)
    cadena_activa = cl.user_session.get("cadena", cadena_con_historial)

    # Inicializar contador de intentos en la sesión si no existe
    intentos = cl.user_session.get("intentos", 0)

    # Mostrar mensaje de "pensando"
    modelo_activo = cl.user_session.get("modelo_activo", "")
    nombre_modelo = get_nombre_modelo(modelo_activo) if modelo_activo else "LLM"
    msg = cl.Message(content=f"🤔 Reflexionando sobre tu pregunta... ({nombre_modelo})")
    await msg.send()

    respuesta_final = None
    es_valida = False

    # Intentar generar una respuesta válida (máximo 2 intentos)
    while intentos < 2 and not es_valida:
        try:
            # Invocar la cadena con el historial de conversación
            resultado = await cadena_activa.ainvoke(
                {"input": message.content},
                config={"configurable": {"session_id": session_id}},
            )
            respuesta_ia = resultado.content
        except Exception as e:
            logger.error("Error al invocar el LLM: %s", str(e))
            respuesta_final = (
                "⚠️ Hubo un problema al conectar con el modelo de IA. "
                "Esto puede deberse a que el proxy OpenCode no está corriendo "
                "o el modelo seleccionado no está disponible.\n\n"
                + RESPUESTA_RESPALDO
            )
            break

        # Limpiar la respuesta de cualquier resto de código
        respuesta_limpia = limpiar_respuesta(respuesta_ia)

        # Validar la respuesta
        es_valida, mensaje_error = validar_respuesta(respuesta_limpia)

        if not es_valida:
            intentos += 1
            cl.user_session.set("intentos", intentos)

            if intentos < 2:
                # Si aún quedan intentos, pedir a la IA que reformule
                mensaje_reformulacion = (
                    f"Tu respuesta anterior no fue adecuada: {mensaje_error} "
                    f"Por favor, reformula siguiendo estrictamente el método "
                    f"socrático: haz solo preguntas guía, sin código, "
                    f"Pregunta original del estudiante: {message.content}"
                )
                # Agregar este mensaje al historial para la próxima iteración
                historial = obtener_historial(session_id)
                historial.add_user_message(mensaje_reformulacion)
            else:
                # Se agotaron los intentos, usar respuesta de respaldo
                respuesta_final = RESPUESTA_RESPALDO
        else:
            # Respuesta válida
            respuesta_final = respuesta_limpia

    # Si después de 2 intentos aún no es válida (por si acaso), usar respaldo
    if respuesta_final is None:
        respuesta_final = RESPUESTA_RESPALDO

    # Resetear el contador de intentos para la próxima pregunta
    cl.user_session.set("intentos", 0)

    # Actualizar el mensaje con la respuesta final
    msg.content = respuesta_final
    await msg.update()
