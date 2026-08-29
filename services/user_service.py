"""
Servicio de gestión de usuarios y autenticación.

Maneja el registro, búsqueda, hashing de contraseñas y validación
de credenciales contra la base de datos Supabase PostgreSQL.
"""

import logging
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import SessionLocal
from models.user import User

logger = logging.getLogger(__name__)


def hashear_password(password: str) -> str:
    """
    Genera un hash seguro para una contraseña usando pbkdf2:sha256.

    Args:
        password: La contraseña en texto plano.

    Returns:
        String con la contraseña hasheada.
    """
    return generate_password_hash(password, method="pbkdf2:sha256")


def verificar_password(password: str, password_hash: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash guardado.

    Args:
        password: La contraseña a verificar.
        password_hash: El hash guardado en la BD.

    Returns:
        True si coincide, False en caso contrario.
    """
    return check_password_hash(password_hash, password)


def buscar_usuario_por_email(email: str) -> Optional[User]:
    """
    Busca un usuario en la base de datos por su correo electrónico.

    Args:
        email: Correo electrónico del usuario.

    Returns:
        Objeto User si existe, None si no se encuentra.
    """
    email_normalizado = email.strip().lower()
    with SessionLocal() as db:
        return db.query(User).filter(User.email == email_normalizado).first()


def crear_usuario(
    email: str,
    password: str,
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
) -> User:
    """
    Registra un nuevo usuario en la base de datos con contraseña hasheada.

    Args:
        email: Correo electrónico del usuario.
        password: Contraseña en texto plano.
        nombre: Nombre del estudiante (opcional).
        apellido: Apellido del estudiante (opcional).

    Returns:
        El objeto User creado.

    Raises:
        ValueError: Si el usuario ya existe.
    """
    email_normalizado = email.strip().lower()
    
    with SessionLocal() as db:
        existente = db.query(User).filter(User.email == email_normalizado).first()
        if existente:
            raise ValueError(f"Ya existe un usuario registrado con el correo {email_normalizado}")

        pwd_hash = hashear_password(password)
        nuevo_usuario = User(
            email=email_normalizado,
            password_hash=pwd_hash,
            nombre=nombre or email_normalizado.split("@")[0].capitalize(),
            apellido=apellido,
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        logger.info("Usuario creado exitosamente: %s (ID: %s)", nuevo_usuario.email, nuevo_usuario.id)
        return nuevo_usuario


def autenticar_o_registrar(email: str, password: str) -> Optional[User]:
    """
    Autentica un usuario existente o lo registra automáticamente si es nuevo.

    Flujo:
    1. Si el usuario existe: verifica la contraseña.
       - Si es correcta -> devuelve el usuario.
       - Si es incorrecta -> devuelve None.
    2. Si el usuario NO existe: crea la cuenta automáticamente y devuelve el nuevo usuario.

    Args:
        email: Correo electrónico (username en Chainlit).
        password: Contraseña enviada.

    Returns:
        Objeto User si la autenticación/registro fue exitoso, None si falló.
    """
    if not email or not password or len(password.strip()) < 4:
        logger.warning("Intento de login fallido: credenciales vacías o contraseña muy corta.")
        return None

    email_normalizado = email.strip().lower()

    with SessionLocal() as db:
        usuario = db.query(User).filter(User.email == email_normalizado).first()

        if usuario:
            # Usuario existente -> verificar contraseña
            if verificar_password(password, usuario.password_hash):
                logger.info("Autenticación exitosa para: %s", usuario.email)
                return usuario
            else:
                logger.warning("Contraseña incorrecta para el usuario: %s", usuario.email)
                return None
        else:
            # Usuario nuevo -> crear automáticamente
            logger.info("Usuario no encontrado. Registrando nueva cuenta para: %s", email_normalizado)
            try:
                pwd_hash = hashear_password(password)
                nombre_defecto = email_normalizado.split("@")[0].capitalize()
                nuevo_usuario = User(
                    email=email_normalizado,
                    password_hash=pwd_hash,
                    nombre=nombre_defecto,
                )
                db.add(nuevo_usuario)
                db.commit()
                db.refresh(nuevo_usuario)
                logger.info("Cuenta creada automáticamente para: %s (ID: %s)", nuevo_usuario.email, nuevo_usuario.id)
                return nuevo_usuario
            except Exception as e:
                db.rollback()
                logger.error("Error al registrar automáticamente el usuario %s: %s", email_normalizado, str(e))
                return None
