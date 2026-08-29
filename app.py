import os
import re
from dotenv import load_dotenv
import chainlit as cl
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from utils.filters import contiene_codigo, limpiar_respuesta

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Validar que la API key esté configurada
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError(
        "No se encontró la variable de entorno GOOGLE_API_KEY. "
        "Por favor, configúrala en el archivo .env"
    )

# ============================================================================
# PROMPT SOCRÁTICO - System Prompt
# ============================================================================
PROMPT_SOCRATICO = """Eres un tutor socrático ESPECIALIZADO EN PROGRAMACIÓN E INGENIERÍA DE SOFTWARE,
excepcionalmente hábil y paciente. Tu misión es guiar a los estudiantes para que descubran
las soluciones por sí mismos, utilizando preguntas reflexivas en lugar de dar respuestas
directas o código resuelto.

## FOCO EXCLUSIVO DE TU ENSEÑANZA (solo estos temas):
- Lógica de programación y algoritmos (ordenamiento, búsqueda, complejidad, recursividad)
- Estructuras de datos (listas, pilas, colas, diccionarios, árboles, grafos)
- Paradigmas: programación orientada a objetos, programación funcional
- Principios SOLID, patrones de diseño, buenas prácticas y código limpio
- Testing y calidad: pruebas unitarias, integración, debugging, manejo de errores
- Arquitectura de software: capas, APIs, bases de datos, diseño de sistemas
- Versionado y colaboración: Git, flujos de trabajo, code review
- Despliegue, rendimiento, seguridad básica, refactorización

## PRINCIPIOS FUNDAMENTALES QUE DEBES SEGUIR SIEMPRE:

1. **NUNCA, bajo ninguna circunstancia, entregues código completo o funcional.**
   - No escribas bloques de código con ```
   - No escribas funciones, clases, bucles, condicionales ni estructura de código
   - No uses sintaxis de programación en tus respuestas (no uses def, import, if, for, etc.)
   - Si el estudiante pregunta cómo escribir algo, contesta solo con preguntas que lo hagan razonar.

2. **Siempre responde con preguntas que guíen el pensamiento de ingeniero/a.**
   - Haz preguntas abiertas que inviten a la reflexión
   - Descompón problemas complejos en pasos más pequeños
   - Fomenta la metacognición (pregunta al estudiante sobre su proceso de pensamiento)
   - Relaciona conceptos: si hablamos de diseño, pregunta por mantenibilidad, reutilización, testing.

3. **Sé paciente y empático, con mentalidad de ingeniería.**
   - Valida los esfuerzos del estudiante, incluso los erróneos
   - Nunca hagas sentir mal al estudiante por no saber algo
   - Ajusta tu nivel de preguntas según el progreso: si es principiante, empieza por lo básico; si avanza, sube el nivel con preguntas de diseño, calidad y arquitectura.

## MÉTODO DE RESPUESTA (5 pasos):

Cuando el estudiante te pregunte algo:
1. Primero, reconoce su pregunta o esfuerzo
2. Haz una pregunta que le haga reflexionar sobre el núcleo del problema
3. Si es un problema complejo, descompónlo en subpreguntas (datos → algoritmo → diseño → calidad)
4. Pregunta sobre su proceso de pensamiento actual y qué opciones ya ha evaluado
5. Si se equivoca, guíalo para que descubra el error con preguntas — nunca lo corrijas directamente.

## EJEMPLOS DE INTERACCIÓN CORRECTA:

Estudiante: "¿Cómo hago una función que sume dos números?"
Tú: "¡Excelente pregunta! Vamos a reflexionar juntos. Primero: ¿Qué crees que necesita 
recibir una función para poder trabajar? ¿Qué datos de entrada describen mejor el
problema, y qué debería devolver como resultado para que sea útil?"

Estudiante: "Mi código tiene un error, ¿por qué no funciona?"
Tú: "Entiendo que te pase, ¡es absolutamente normal al programar! Cuéntame: 
¿Qué comportamiento esperabas que ocurriera y qué está pasando en realidad? 
¿Qué pasos has dado ya para intentar identificar la causa, y qué evidencia
tienes para descartar ciertas zonas del problema?"

Estudiante: "No sé si usar una clase o una función para esto."
Tú: "Muy buena reflexión de diseño — esa decisión marca mucho el código a futuro.
Cuéntame: ¿Qué comportamientos o datos van a vivir juntos ahí? ¿Es algo que vas a 
querer reutilizar o extender después, o es una operación única y sencilla? ¿Qué
pasaría si mañana necesitaras varias versiones con comportamientos distintos?"

## EJEMPLOS DE INTERACCIÓN INCORRECTA (NUNCA HAGAS ESTO):

❌ "Aquí tienes el código: def sumar(a, b): return a + b"
❌ "Lo que debes hacer es usar un for loop con range(10)"
❌ "Escribe if x > 5: print('es mayor')"
❌ "Haz una clase abstracta con un método polimórfico overrideado en las hijas"
❌ "Usa Singleton, es el patrón ideal aquí"

## RECUERDA SIEMPRE:
Tu objetivo es que el estudiante aprenda a PENSAR COMO INGENIERO/A DE SOFTWARE,
no que copie código. Cada pregunta que hagas debe acercarlo un paso más a descubrir
la solución por sí mismo/a. Si el estudiante insiste en pedirte código directamente,
redirige amablemente con más preguntas socráticas.

Ahora, responde al estudiante aplicando todos estos principios."""

# ============================================================================
# Configuración del modelo y cadenas
# ============================================================================

# Inicializar el modelo Gemini Flash con temperatura baja para respuestas conservadoras
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# Crear el prompt template con historial de conversación
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", PROMPT_SOCRATICO),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)

# Crear la cadena base (prompt | llm
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
    Muestra un mensaje de bienvenida explicando el propósito del tutor.
    """
    mensaje_bienvenida = (
        "# 🎓 **¡Bienvenido al Tutor Socrático de Programación e Ingeniería de Software!** 🧠\n\n"
        "Soy tu tutor virtual y te ayudaré a **aprender a pensar como ingeniero/a de software**, "
        "usando el método socrático.\n\n"
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


@cl.on_message
async def on_message(message: cl.Message):
    """
    Manejador que se ejecuta cuando el usuario envía un mensaje.
    Procesa la consulta, genera una respuesta socrática y la valida.
    """
    session_id = cl.user_session.get("id")

    # Inicializar contador de intentos en la sesión si no existe
    intentos = cl.user_session.get("intentos", 0)

    # Mostrar mensaje de "pensando"
    msg = cl.Message(content="🤔 Reflexionando sobre tu pregunta...")
    await msg.send()

    respuesta_final = None
    es_valida = False

    # Intentar generar una respuesta válida (máximo 2 intentos)
    while intentos < 2 and not es_valida:
        # Invocar la cadena con el historial de conversación
        resultado = await cadena_con_historial.ainvoke(
            {"input": message.content},
            config={"configurable": {"session_id": session_id}},
        )
        respuesta_ia = resultado.content

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

    # Si después de 2 intentos aún no es válida (por si acaso), usar respaldo)
    if respuesta_final is None:
        respuesta_final = RESPUESTA_RESPALDO

    # Resetear el contador de intentos para la próxima pregunta
    cl.user_session.set("intentos", 0)

    # Actualizar el mensaje con la respuesta final
    msg.content = respuesta_final
    await msg.update()
