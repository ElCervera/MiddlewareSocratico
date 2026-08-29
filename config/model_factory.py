"""
Fábrica de modelos LLM para el Middleware Socrático.

Permite seleccionar entre múltiples modelos (Google Gemini, OpenCode Zen gratuitos, etc.)
mediante variables de entorno, con fallback automático a Gemini directo si el proxy
OpenCode no está disponible.

Uso:
    from config.model_factory import get_llm, switch_model, MODELOS_DISPONIBLES
    llm = get_llm(temperature=0.3)
"""

import os
import logging
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

# ============================================================================
# Catálogo de modelos disponibles
# ============================================================================

MODELOS_DISPONIBLES = {
    # --- Modelos de Google (a través del proxy OpenCode) ---
    "google/gemini-1.5-flash": {
        "nombre": "🟦 Gemini 1.5 Flash (Google)",
        "descripcion": "Modelo predeterminado rápido y eficiente de Google.",
        "requiere_proxy": True,
        "requiere_google_key": True,
    },
    "google/gemini-3.6-flash": {
        "nombre": "🟦 Gemini 3.6 Flash (Google)",
        "descripcion": "Modelo reciente y potente de Google.",
        "requiere_proxy": True,
        "requiere_google_key": True,
    },
    "google/gemini-2.5-pro": {
        "nombre": "🟦 Gemini 2.5 Pro (Google)",
        "descripcion": "Modelo avanzado de Google con mayor capacidad de razonamiento.",
        "requiere_proxy": True,
        "requiere_google_key": True,
    },
    # --- Modelos gratuitos de OpenCode Zen ---
    "opencode-zen/deepseek-v4-flash-free": {
        "nombre": "🟢 DeepSeek V4 Flash (Gratis)",
        "descripcion": "Modelo rápido de DeepSeek, excelente en razonamiento y código.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    "opencode-zen/qwen3.6-plus-free": {
        "nombre": "🟢 Qwen 3.6 Plus (Gratis)",
        "descripcion": "Modelo de Alibaba con fuerte capacidad multilingüe.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    "opencode-zen/nemotron-3-super-free": {
        "nombre": "🟢 Nemotron 3 Super (Gratis)",
        "descripcion": "Modelo de NVIDIA optimizado para tareas de asistencia.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    "opencode-zen/mimo-v2.5-free": {
        "nombre": "🟢 MiMo V2.5 (Gratis)",
        "descripcion": "Modelo compacto con buen rendimiento en razonamiento.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    "opencode-zen/minimax-m2.5-free": {
        "nombre": "🟢 MiniMax M2.5 (Gratis)",
        "descripcion": "Modelo versátil con buenas capacidades generales.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    "opencode-zen/big-pickle": {
        "nombre": "🟢 Big Pickle (Gratis)",
        "descripcion": "Modelo experimental de alto rendimiento en OpenCode Zen.",
        "requiere_proxy": True,
        "requiere_google_key": False,
    },
    # --- Fallback directo (sin proxy) ---
    "gemini-1.5-flash": {
        "nombre": "🟡 Gemini 1.5 Flash (Directo - Fallback)",
        "descripcion": "Conexión directa a Google AI Studio, no requiere proxy.",
        "requiere_proxy": False,
        "requiere_google_key": True,
    },
}

# Modelo por defecto si ACTIVE_MODEL no está definido
MODELO_POR_DEFECTO = "google/gemini-1.5-flash"

# Modelo de fallback cuando el proxy no está disponible
MODELO_FALLBACK = "gemini-1.5-flash"


def _crear_llm_proxy(model_id: str, temperature: float = 0.3) -> ChatOpenAI:
    """
    Crea una instancia de ChatOpenAI apuntando al proxy local de OpenCode.

    Args:
        model_id: Identificador del modelo (ej. "google/gemini-3.6-flash").
        temperature: Temperatura para la generación de respuestas.

    Returns:
        Instancia de ChatOpenAI configurada.

    Raises:
        ValueError: Si faltan variables de entorno requeridas.
    """
    base_url = os.getenv("OPENCODE_BASE_URL", "http://127.0.0.1:4010/v1")
    api_key = os.getenv("OPENCODE_API_KEY", "opencode-proxy")

    info_modelo = MODELOS_DISPONIBLES.get(model_id, {})

    # Si el modelo requiere GOOGLE_API_KEY, verificar que esté disponible
    if info_modelo.get("requiere_google_key") and not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            f"El modelo '{model_id}' requiere GOOGLE_API_KEY pero no está configurada."
        )

    logger.info(
        "Creando LLM via proxy OpenCode: modelo=%s, base_url=%s",
        model_id,
        base_url,
    )

    return ChatOpenAI(
        model=model_id,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=base_url,
        request_timeout=5,
        max_retries=1,
    )


def _crear_llm_fallback(temperature: float = 0.3):
    """
    Crea una instancia directa de ChatGoogleGenerativeAI como fallback.

    Args:
        temperature: Temperatura para la generación de respuestas.

    Returns:
        Instancia de ChatGoogleGenerativeAI configurada.

    Raises:
        ValueError: Si GOOGLE_API_KEY no está configurada.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError(
            "No se encontró GOOGLE_API_KEY. Es necesaria para el fallback a Gemini."
        )

    logger.info("Creando LLM fallback directo: gemini-1.5-flash (y gemini-3.6-flash)")

    gemini_15 = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=temperature,
        google_api_key=google_api_key,
    )
    gemini_36 = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=temperature,
        google_api_key=google_api_key,
    )
    return gemini_15.with_fallbacks([gemini_36])


def get_llm(model_id: str | None = None, temperature: float = 0.3):
    """
    Obtiene una instancia del LLM configurado con fallback automático.

    Si el modelo seleccionado requiere el proxy OpenCode y este no está
    disponible, el sistema automáticamente cae al fallback (Gemini directo).

    Args:
        model_id: ID del modelo a usar. Si es None, lee ACTIVE_MODEL del .env.
        temperature: Temperatura para la generación (default 0.3).

    Returns:
        Instancia del LLM con fallback configurado.
    """
    if model_id is None:
        model_id = os.getenv("ACTIVE_MODEL", MODELO_POR_DEFECTO)

    # Validar que el modelo exista en el catálogo
    if model_id not in MODELOS_DISPONIBLES:
        logger.warning(
            "Modelo '%s' no está en el catálogo. Usando modelo por defecto '%s'.",
            model_id,
            MODELO_POR_DEFECTO,
        )
        model_id = MODELO_POR_DEFECTO

    info_modelo = MODELOS_DISPONIBLES[model_id]

    # Si el modelo NO requiere proxy, usar conexión directa
    if not info_modelo["requiere_proxy"]:
        logger.info("Usando modelo directo (sin proxy): %s", model_id)
        return _crear_llm_fallback(temperature=temperature)

    # Si requiere proxy, crear con fallback automático
    try:
        llm_proxy = _crear_llm_proxy(model_id, temperature=temperature)
        llm_fallback = _crear_llm_fallback(temperature=temperature)

        logger.info(
            "LLM configurado: %s (con fallback a gemini-1.5-flash)",
            info_modelo["nombre"],
        )

        # .with_fallbacks() de LangChain: si el proxy falla, usa Gemini directo
        return llm_proxy.with_fallbacks([llm_fallback])

    except Exception as e:
        logger.error(
            "Error al crear LLM proxy para '%s': %s. Usando fallback directo.",
            model_id,
            str(e),
        )
        return _crear_llm_fallback(temperature=temperature)


def get_nombre_modelo(model_id: str) -> str:
    """
    Obtiene el nombre legible de un modelo a partir de su ID.

    Args:
        model_id: Identificador del modelo.

    Returns:
        Nombre legible del modelo, o el ID si no se encuentra.
    """
    info = MODELOS_DISPONIBLES.get(model_id)
    if info:
        return info["nombre"]
    return model_id


def get_lista_modelos() -> list[str]:
    """
    Retorna la lista de IDs de todos los modelos disponibles.

    Returns:
        Lista de strings con los IDs de modelos.
    """
    return list(MODELOS_DISPONIBLES.keys())


def get_opciones_selector() -> list[str]:
    """
    Retorna las opciones formateadas para el selector de Chainlit.
    Cada opción es el ID del modelo (usado como value en el Select widget).

    Returns:
        Lista de IDs de modelos para el widget Select de Chainlit.
    """
    return list(MODELOS_DISPONIBLES.keys())
