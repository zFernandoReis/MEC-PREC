"""Prepara o banco antes de substituir o processo pelo servidor HTTP."""

import os
import subprocess
import sys


def main() -> None:
    for module in ("app.bootstrap.create_tables", "app.bootstrap.migrate_notification_type"):
        print(f"[startup] Executando {module}", flush=True)
        subprocess.run([sys.executable, "-m", module], check=True)
    print("[startup] Executando todos os testes do projeto", flush=True)
    subprocess.run([
        sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
        "--tb=short",
    ], check=True)
    print("[startup] Testes aprovados; iniciando ingestão inicial", flush=True)
    subprocess.run([sys.executable, "-m", "app.bootstrap.seed_initial_data"], check=True)
    print("[startup] Preparação concluída; iniciando API", flush=True)
    os.execvp(sys.executable, [
        sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000",
    ])


if __name__ == "__main__":
    main()
