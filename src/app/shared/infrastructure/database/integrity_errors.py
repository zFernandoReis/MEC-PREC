import re

from sqlalchemy.exc import IntegrityError


CONFLICTS = {
    "23505": ("unique_violation", "Já existe um registro com os campos informados."),
    "23503": (
        "foreign_key_violation",
        "O registro relacionado não existe ou está sendo utilizado por outro registro.",
    ),
    "23502": ("not_null_violation", "Um campo obrigatório não foi informado."),
    "23514": ("check_violation", "Os dados não atendem a uma regra de validação do banco."),
    "23P01": ("exclusion_violation", "Os dados conflitam com outro registro existente."),
}


def integrity_error_details(exc: IntegrityError) -> dict:
    """Extrai metadados do driver sem retornar SQL, parâmetros ou valores dos dados."""
    errors = []
    current = exc.orig
    while current is not None and all(current is not error for error in errors):
        errors.append(current)
        current = current.__cause__

    def metadata(name):
        for error in errors:
            for source in (error, getattr(error, "diag", None)):
                value = getattr(source, name, None)
                if isinstance(value, str) and value:
                    return value
        return None

    sqlstate = metadata("sqlstate") or metadata("pgcode")
    code, message = CONFLICTS.get(sqlstate, (
        "integrity_conflict", "Dados em conflito com as restrições do banco de dados.",
    ))
    column = metadata("column_name")
    fields = [column] if column else []
    detail = metadata("detail") or metadata("message_detail")
    if not fields and detail:
        match = re.search(r"Key \(([^)]+)\)=", detail)
        if match:
            fields = [field.strip().strip('"') for field in match[1].split(",")]

    # SQLite fornece os nomes das colunas na mensagem em vez de metadados.
    if sqlstate is None and errors:
        sqlite_code = getattr(errors[0], "sqlite_errorname", None)
        sqlite_codes = {
            "SQLITE_CONSTRAINT_UNIQUE": "23505",
            "SQLITE_CONSTRAINT_PRIMARYKEY": "23505",
            "SQLITE_CONSTRAINT_FOREIGNKEY": "23503",
            "SQLITE_CONSTRAINT_NOTNULL": "23502",
            "SQLITE_CONSTRAINT_CHECK": "23514",
        }
        if sqlite_code in sqlite_codes:
            code, message = CONFLICTS[sqlite_codes[sqlite_code]]
            if sqlite_codes[sqlite_code] in ("23505", "23502"):
                _, _, columns = str(errors[0]).partition(": ")
                fields = [item.strip().rsplit(".", 1)[-1] for item in columns.split(",") if item]

    return {
        "detail": message,
        "error": {
            "code": code,
            "fields": fields,
            "table": metadata("table_name"),
            "constraint": metadata("constraint_name"),
        },
    }
