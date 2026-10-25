import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock

from app.bootstrap import notification_scheduler, start_server


async def test_cycle_runs_both_jobs_with_separate_sessions(monkeypatch):
    sessions = [MagicMock(), MagicMock()]
    contexts = [AsyncMock(), AsyncMock()]
    for context, session in zip(contexts, sessions):
        context.__aenter__.return_value = session
    factory = MagicMock(side_effect=contexts)
    upcoming = MagicMock()
    upcoming.__name__ = "NotifyUpcomingOrdersJob"
    upcoming.return_value.execute = AsyncMock(side_effect=RuntimeError("database unavailable"))
    overdue = MagicMock()
    overdue.__name__ = "NotifyOverdueOrdersJob"
    overdue.return_value.execute = AsyncMock()
    monkeypatch.setattr(notification_scheduler, "AsyncSessionLocal", factory)
    monkeypatch.setattr(notification_scheduler, "NotifyUpcomingOrdersJob", upcoming)
    monkeypatch.setattr(notification_scheduler, "NotifyOverdueOrdersJob", overdue)

    await notification_scheduler.run_cycle(days_before=5, batch_size=20)

    upcoming.assert_called_once_with(sessions[0])
    upcoming.return_value.execute.assert_awaited_once_with(days_before=5, batch_size=20)
    overdue.assert_called_once_with(sessions[1])
    overdue.return_value.execute.assert_awaited_once_with(batch_size=20)
    for context in contexts:
        context.__aexit__.assert_awaited_once()


def test_preparation_failure_prevents_server_start(monkeypatch):
    import subprocess

    import pytest

    prepare = MagicMock(side_effect=subprocess.CalledProcessError(1, "create_tables"))
    start = MagicMock()
    monkeypatch.setattr(start_server.subprocess, "run", prepare)
    monkeypatch.setattr(start_server.os, "execvp", start)
    with pytest.raises(subprocess.CalledProcessError):
        start_server.main()
    start.assert_not_called()


async def test_scheduler_waits_one_hour_and_stops_gracefully(monkeypatch):
    loop = MagicMock()
    loop.time.side_effect = [100, 110, 3700]
    callbacks = {}
    loop.add_signal_handler.side_effect = lambda sig, callback: callbacks.update({sig: callback})
    cycles = 0

    async def cycle(**options):
        nonlocal cycles
        cycles += 1
        if cycles == 2:
            callbacks[signal.SIGTERM]()

    async def wait(awaitable, *, timeout):
        # Fecha a coroutine sem uma espera real de uma hora.
        awaitable.close()
        assert timeout == 3590
        raise TimeoutError

    dispose = AsyncMock()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)
    monkeypatch.setattr(asyncio, "wait_for", wait)
    monkeypatch.setattr(notification_scheduler, "run_cycle", cycle)
    monkeypatch.setattr(notification_scheduler, "engine", MagicMock(dispose=dispose))

    await notification_scheduler.run(days_before=3, batch_size=100)

    assert cycles == 2
    dispose.assert_awaited_once()
    assert loop.remove_signal_handler.call_count == 2
