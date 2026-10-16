import inspect
import io
import logging

import pytest

from app.shared.infrastructure.logging import configure_logging, logger
import app.shared.infrastructure.logging as app_logging


@pytest.fixture
def output(monkeypatch):
    stream = io.StringIO()
    isolated_logger = logging.Logger("app.test")
    monkeypatch.setattr(app_logging, "logger", isolated_logger)
    monkeypatch.setitem(globals(), "logger", isolated_logger)
    handler = logging.StreamHandler(stream)
    handler.set_name("app.console")
    handler.setFormatter(logging.Formatter(app_logging.LOG_FORMAT))
    isolated_logger.addHandler(handler)
    yield stream
    for handler in logger.handlers:
        handler.close()


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO])
def test_logging_includes_actual_call_location_and_comment(output, level):
    configure_logging(level)
    line = inspect.currentframe().f_lineno + 1
    logger.log(level, "Processando item %s", "ABC")

    message = output.getvalue()
    assert "arquivo=test_logging.py" in message
    assert "metodo=test_logging_includes_actual_call_location_and_comment" in message
    assert f"linha={line} | Processando item ABC" in message
    assert logging.getLevelName(level) in message


def test_configuration_creates_console_handler_and_emits_debug(monkeypatch, capsys):
    isolated_logger = logging.Logger("app.test.console")
    monkeypatch.setattr(app_logging, "logger", isolated_logger)
    try:
        configure_logging("DEBUG")
        configure_logging("DEBUG")
        isolated_logger.debug("Detalhes do processamento")
        assert len(isolated_logger.handlers) == 1
        assert capsys.readouterr().err.count("Detalhes do processamento") == 1
    finally:
        for handler in isolated_logger.handlers:
            handler.close()


def test_configuration_is_idempotent_and_respects_level(output):
    configure_logging()
    configure_logging(logging.WARNING)
    logger.info("Mensagem ignorada")
    logger.warning("Aviso")

    assert len(logger.handlers) == 1
    assert output.getvalue().count("Aviso") == 1
    assert "Mensagem ignorada" not in output.getvalue()


def test_exception_includes_traceback(output):
    configure_logging()
    try:
        raise ValueError("Falha de exemplo")
    except ValueError:
        logger.exception("Erro ao processar item")

    assert "Erro ao processar item" in output.getvalue()
    assert "Traceback" in output.getvalue()
    assert "ValueError: Falha de exemplo" in output.getvalue()
