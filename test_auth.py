"""
Script de prueba para el servicio de autenticación y usuarios.
"""

import sys
from services.user_service import (
    hashear_password,
    verificar_password,
    crear_usuario,
    buscar_usuario_por_email,
    autenticar_o_registrar,
)


def test_auth():
    print("[+] Probando hashing de contraseñas...")
    raw_pwd = "PasswordPrueba123*"
    hashed = hashear_password(raw_pwd)
    assert verificar_password(raw_pwd, hashed), "Error: La contraseña debió coincidir"
    assert not verificar_password("PasswordErrada", hashed), "Error: La contraseña errada no debió coincidir"
    print("[OK] Hashing y verificación de contraseñas funcionando correctamente.")

    email_test = "estudiante_test@socratico.edu"
    
    # Limpiar usuario anterior si existe
    existente = buscar_usuario_por_email(email_test)
    if existente:
        print(f"[+] Usuario de prueba previo encontrado: {existente.email}")

    print(f"[+] Probando autenticar_o_registrar para '{email_test}'...")
    user = autenticar_o_registrar(email_test, raw_pwd)
    assert user is not None, "Error: No se creó ni retornó el usuario"
    print(f"[OK] Usuario autenticado/creado exitosamente. ID: {user.id}, Nombre: {user.nombre}")

    print("[+] Probando autenticación con contraseña incorrecta...")
    bad_auth = autenticar_o_registrar(email_test, "PasswordWrong")
    assert bad_auth is None, "Error: Debió rechazar la contraseña incorrecta"
    print("[OK] Contraseña incorrecta rechazada correctamente.")

    print("\n[SUCCESS] ¡Todas las pruebas del servicio de autenticación pasaron con éxito!")


if __name__ == "__main__":
    test_auth()
