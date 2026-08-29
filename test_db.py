"""
Script de verificación de conexión y tablas en Supabase PostgreSQL.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import inspect
from config.database import engine, get_db
from models import User, Conversation, Message, GuardrailsLog

load_dotenv()


def main():
    print("[+] Conectando a Supabase PostgreSQL...")
    inspector = inspect(engine)
    tablas = inspector.get_table_names()

    print("[OK] Conexion exitosa. Tablas detectadas en la base de datos:")
    for t in tablas:
        print(f"   - {t}")

    tablas_esperadas = ["users", "conversations", "messages", "guardrails_log", "alembic_version"]
    faltantes = [t for t in tablas_esperadas if t not in tablas]

    if not faltantes:
        print("\n[SUCCESS] Sprint 0 completado con exito! Todas las tablas estan creadas en Supabase.")
    else:
        print(f"\n[WARNING] Faltan algunas tablas: {faltantes}")


if __name__ == "__main__":
    main()
