import re


def contiene_codigo(texto: str) -> bool:
    """
    Verifica si el texto contiene bloques de código o palabras clave
    de programación que indiquen que la IA está entregando código resuelto.

    Args:
        texto: El texto a analizar.

    Returns:
        True si contiene código, False en caso contrario.
    """
    # Verificar bloques de código con triple backticks
    if re.search(r"```[\s\S]*?```", texto):
        return True

    # Verificar bloques de código con backticks simples (inline)
    # Solo marcar si hay múltiples o si contienen patrones de código
    inline_code = re.findall(r"`([^`]+)`", texto)
    for code in inline_code:
        # Si el inline code tiene más de una estructura de código, marcarlo
        if re.search(
            r"(def\s+\w+|import\s+|class\s+\w+|for\s+.+in\s+|while\s+.+:)",
            code,
        ):
            return True

    # Lista de palabras clave de programación (Python principalmente)
    palabras_clave = [
        r"\bdef\s+\w+\s*\(",  # Definición de funciones
        r"\bimport\s+\w+",  # Importaciones
        r"\bfrom\s+\w+\s+import",  # From import
        r"\bclass\s+\w+",  # Clases
        r"\bif\s+.+:",  # Condicional if
        r"\belif\s+.+:",  # Condicional elif
        r"\belse\s*:",  # Condicional else
        r"\bfor\s+.+in\s+.+:",  # Bucles for
        r"\bwhile\s+.+:",  # Bucles while
        r"\breturn\s+",  # Return
        r"\bprint\s*\(",  # Print
        r"\btry\s*:",  # Try
        r"\bexcept\s*:",  # Except
        r"\bwith\s+.+:",  # With
        r"\blambda\s+",  # Lambda
        r"\basync\s+def\s+\w+",  # Async def
        r"\bawait\s+",  # Await
        r"->\s*\w+",  # Type hints de retorno
        r":\s*\w+(\[.+\])?\s*=",  # Type hints en variables
        r"\bpass\b",  # Pass statement
        r"\bbreak\b",  # Break
        r"\bcontinue\b",  # Continue
        r"\braise\s+",  # Raise exceptions
        r"\bassert\s+",  # Assert
        r"\bglobal\s+",  # Global
        r"\bnonlocal\s+",  # Nonlocal
        r"\bdel\s+",  # Delete
        r"\bin\s+range\s*\(",  # Range
    ]

    # Verificar si alguna palabra clave aparece en el texto
    for patron in palabras_clave:
        if re.search(patron, texto):
            return True

    return False


def limpiar_respuesta(texto: str) -> str:
    """
    Elimina bloques de código y líneas que parezcan código del texto,
    devolviendo solo el texto guía.

    Args:
        texto: El texto a limpiar.

    Returns:
        El texto sin código.
    """
    # Eliminar bloques de código con triple backticks
    texto_limpio = re.sub(r"```[\s\S]*?```", "", texto)

    # Eliminar inline code que parezca código de programación
    def reemplazar_inline(match):
        codigo = match.group(1)
        # Si parece código, eliminarlo; si no, dejarlo
        if re.search(
            r"(def\s+\w+|import\s+|class\s+\w+|for\s+.+in\s+|while\s+.+:)",
            codigo,
        ):
            return ""
        return match.group(0)

    texto_limpio = re.sub(r"`([^`]+)`", reemplazar_inline, texto_limpio)

    # Eliminar líneas que comiencen con patrones de código
    lineas = texto_limpio.split("\n")
    lineas_limpias = []

    for linea in lineas:
        # Saltar líneas vacías al principio
        if not linea.strip():
            if lineas_limpias and lineas_limpias[-1].strip() == "":
                continue  # Evitar múltiples líneas vacías consecutivas
            lineas_limpias.append(linea)
            continue

        # Patrones que indican que la línea es código
        patrones_linea_codigo = [
            r"^\s*def\s+\w+\s*\(",
            r"^\s*import\s+\w+",
            r"^\s*from\s+\w+\s+import",
            r"^\s*class\s+\w+",
            r"^\s*if\s+.+:",
            r"^\s*elif\s+.+:",
            r"^\s*else\s*:",
            r"^\s*for\s+.+in\s+.+:",
            r"^\s*while\s+.+:",
            r"^\s*return\s+",
            r"^\s*print\s*\(",
            r"^\s*try\s*:",
            r"^\s*except\s*:",
            r"^\s*with\s+.+:",
            r"^\s*lambda\s+",
            r"^\s*async\s+def\s+\w+",
            r"^\s*await\s+",
            r"^\s*pass\b",
            r"^\s*break\b",
            r"^\s*continue\b",
            r"^\s*raise\s+",
            r"^\s*assert\s+",
            r"^\s*#\s*",  # Comentarios
            r"^\s*>>>",  # Prompt de REPL
            r"^\s*\.\.\.",  # Continuación de REPL
        ]

        es_codigo = False
        for patron in patrones_linea_codigo:
            if re.match(patron, linea):
                es_codigo = True
                break

        if not es_codigo:
            lineas_limpias.append(linea)

    # Unir las líneas limpias
    texto_limpio = "\n".join(lineas_limpias)

    # Eliminar múltiples líneas vacías consecutivas (max 2)
    texto_limpio = re.sub(r"\n{3,}", "\n\n", texto_limpio)

    # Eliminar espacios en blanco al inicio y final
    texto_limpio = texto_limpio.strip()

    return texto_limpio
