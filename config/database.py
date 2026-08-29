"""
Módulo de configuración de la base de datos.

Inicializa el engine de SQLAlchemy y la sesión a partir de la variable
de entorno DATABASE_URL, apuntando a PostgreSQL en Supabase.

TODO (Sprint 0): Completar la inicialización y validar la conexión contra
una instancia real de Supabase. Aquí se usará el modelo asincrónico si
se requiere en un futuro, pero por defecto empezamos con sync dado que
SQLAlchemy 2.x funciona perfectamente en Chainlit dentro de llamadas
async gracias a run_in_executor.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://usuario_placeholder:password_placeholder@localhost:5432/placeholder"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db():
    """
    Generador que entrega una sesión de BD y la cierra al terminar.

    Uso típico:
        with get_db() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
