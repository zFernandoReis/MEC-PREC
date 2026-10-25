"""Importa os arquivos de dados exclusivamente pelos endpoints HTTP da API."""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from pydantic import ValidationError

from app.modules.quotes.application.dtos.budget_dto import CreateBudgetDTO
from app.modules.quotes.application.dtos.stock_dto import CreateStockDTO
from app.modules.users.application.dtos.user_dto import CreateUserDTO
from app.modules.users.application.dtos.vehicle_dto import CreateVehicleDTO


# A ordem respeita as dependências entre as entidades.
RESOURCES = {
    "users": CreateUserDTO,
    "stock": CreateStockDTO,
    "vehicles": CreateVehicleDTO,
    "budgets": CreateBudgetDTO,
}
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "dados"


class IngestionError(Exception):
    """Falha de entrada ou de comunicação; a ingestão deve parar."""


def load_records(data_dir: Path, resources: list[str], *, user_password: str | None = None) -> dict[str, list[dict]]:
    """Valida todos os arquivos selecionados antes de permitir qualquer POST."""
    records = {}
    errors = []
    for resource, schema in RESOURCES.items():
        if resource not in resources:
            continue
        path = data_dir / f"{resource}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: não foi possível ler o JSON ({type(exc).__name__}).")
            continue
        if not isinstance(data, list):
            errors.append(f"{path}: esperado um array de objetos JSON.")
            continue
        records[resource] = []
        for index, item in enumerate(data, start=1):
            try:
                if resource == "users" and isinstance(item, dict) and user_password:
                    item = {"password": user_password, **item}
                validated = schema.model_validate(item)
                payload = validated.model_dump(mode="json")
                if isinstance(validated, CreateUserDTO):
                    # SecretStr protege logs/repr; envie a senha real somente no corpo HTTP.
                    payload["password"] = validated.password.get_secret_value()
            except ValidationError as exc:
                # Não exibe valores de entrada que possam conter dados pessoais.
                for error in exc.errors(include_input=False, include_url=False):
                    field = ".".join(map(str, error["loc"])) or "registro"
                    errors.append(
                        f"{path.name}, registro {index}, {field}: {error['type']}"
                    )
            else:
                records[resource].append(payload)
    for resource, fields, parent in (
        ("vehicles", ("owner_id",), "users"),
        ("budgets", ("technical_id", "client_id"), "users"),
        ("budgets", ("vehicle_id",), "vehicles"),
    ):
        if parent not in records:
            continue
        for index, record in enumerate(records.get(resource, []), start=1):
            for field in fields:
                if not 1 <= record[field] <= len(records[parent]):
                    errors.append(
                        f"{resource}.json, registro {index}, {field}: "
                        f"deve corresponder a uma posição de {parent}.json."
                    )
    if errors:
        raise IngestionError("Validação falhou; nenhum dado foi enviado.\n" + "\n".join(errors))
    return records


def ingest(client: httpx.Client, records: dict[str, list[dict]]) -> int:
    """Envia um POST por registro e para na primeira falha, sem repetir POSTs."""
    created = 0
    user_ids: dict[int, int] = {}
    vehicle_ids: dict[int, int] = {}
    for resource in RESOURCES:
        for index, record in enumerate(records.get(resource, []), start=1):
            payload = dict(record)
            # Nos arquivos fornecidos, os IDs de origem são as posições (1-based)
            # em users.json. O banco pode gerar IDs diferentes dessas posições.
            if "users" in records:
                fields = {
                    "vehicles": ("owner_id",),
                    "budgets": ("technical_id", "client_id"),
                }.get(resource, ())
                for field in fields:
                    source_id = payload[field]
                    if source_id not in user_ids:
                        raise IngestionError(
                            f"{resource}.json, registro {index}: {field} não corresponde "
                            f"a uma posição de users.json. Criados nesta execução: {created}."
                        )
                    payload[field] = user_ids[source_id]
            if resource == "budgets" and "vehicles" in records:
                payload["vehicle_id"] = vehicle_ids[payload["vehicle_id"]]
            context = f"{resource}.json, registro {index}"
            try:
                response = client.post(resource, json=payload)
            except httpx.HTTPError as exc:
                raise IngestionError(
                    f"{context}: falha HTTP ({type(exc).__name__}). "
                    f"Criações confirmadas: {created}. O último POST pode ter sido persistido; "
                    "consulte a API antes de tentar novamente."
                ) from exc
            if response.status_code != 201:
                # Corpos de erro da API podem repetir CPF, e-mail e endereço.
                raise IngestionError(
                    f"{context}: POST /{resource} retornou HTTP {response.status_code}; "
                    f"esperado 201. Criações confirmadas: {created}. "
                    "Consulte os logs da API; não há rollback dos POSTs anteriores."
                )
            created += 1
            if resource in ("users", "vehicles"):
                id_field = "id" if resource == "users" else "vehicle_id"
                try:
                    identifier = response.json()[id_field]
                    if type(identifier) is not int or identifier < 1:
                        raise ValueError("ID inválido")
                    id_map = user_ids if resource == "users" else vehicle_ids
                    id_map[index] = identifier
                except (ValueError, KeyError, TypeError) as exc:
                    raise IngestionError(
                        f"{context}: resposta 201 sem {id_field} inteiro positivo. "
                        f"Criações confirmadas: {created}; ingestão interrompida."
                    ) from exc
            print(f"{context}: criado (HTTP 201).")
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000",
                        help="URL da API (padrão: http://127.0.0.1:8000).")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="Diretório com os arquivos <recurso>.json.")
    parser.add_argument("--resources", nargs="+", choices=list(RESOURCES),
                        default=list(RESOURCES), help="Recursos a importar (padrão: todos).")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Timeout HTTP em segundos (padrão: 30).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Valida os arquivos sem enviar requisições.")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout deve ser positivo.")
    try:
        records = load_records(
            args.data_dir, args.resources, user_password=os.environ.get("MEC_INITIAL_PASSWORD"),
        )
        if args.dry_run:
            print(f"Validação concluída: {sum(map(len, records.values()))} registros. Nenhum POST enviado.")
            return 0
        token = os.environ.get("MEC_ACCESS_TOKEN")
        if not token:
            raise IngestionError("Defina MEC_ACCESS_TOKEN com um access token de administrador antes de importar.")
        with httpx.Client(
            base_url=args.base_url.rstrip("/") + "/", timeout=args.timeout,
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            created = ingest(client, records)
        print(f"Ingestão concluída: {created} registros criados pela API.")
        return 0
    except (IngestionError, httpx.InvalidURL) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
