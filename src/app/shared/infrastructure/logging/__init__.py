"""Logging compartilhado da aplicação, com contexto automático da chamada."""

import logging


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | arquivo=%(filename)s | "
    "metodo=%(funcName)s | linha=%(lineno)d | %(message)s"
)

logger = logging.getLogger("app")


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configura a saída de console sem duplicar handlers em novas chamadas."""
    logger.setLevel(level)
    if not any(handler.get_name() == "app.console" for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.set_name("app.console")
        logger.addHandler(handler)
    logger.propagate = False
