import sys
import subprocess


def run_command(command):
    """Ejecuta un comando en la consola de Windows y retorna el código de salida."""
    try:
        result = subprocess.run(command, shell=True)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n[!] Ejecución cancelada por el usuario.")
        sys.exit(1)


def main():
    print("=" * 60)
    print("      SGI SALUD - SUITE DE PRUEBAS AUTOMATIZADAS")
    print("=" * 60)
    print("1. Ejecutar todos los tests (Rápido)")
    print("2. Ejecutar tests CON reporte de cobertura (pytest-cov)")
    print("3. Ejecutar tests con cobertura y generar reporte HTML")
    print("4. Salir")
    print("-" * 60)

    opcion = input("Selecciona una opción (1-4): ").strip()

    if opcion == "1":
        cmd = "pytest -v"
    elif opcion == "2":
        cmd = "pytest --cov=src --cov-report=term-missing"
    elif opcion == "3":
        cmd = "pytest --cov=src --cov-report=term-missing --cov-report=html"
    elif opcion == "4":
        print("Saliendo...")
        sys.exit(0)
    else:
        print("[!] Opción inválida. Saliendo.")
        sys.exit(1)

    print(f"\n[>] Ejecutando: {cmd}\n")
    return_code = run_command(cmd)

    if opcion == "3" and return_code == 0:
        print("\n[✓] Reporte HTML generado en la carpeta 'htmlcov/index.html'")

    sys.exit(return_code)


if __name__ == "__main__":
    main()