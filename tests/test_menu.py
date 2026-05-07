from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.interfaces.menu.menu import MenuInterface
from tests.fakes import FakeRuntime, FakeSystem


class StubService:
    def __init__(self, code: int, name: str) -> None:
        self.code = code
        self.name = name


class StubManager:
    def __init__(self) -> None:
        self.registry = {1: StubService(1, "Firewall")}
        self.last_options = None

    def execute(self, options):
        self.last_options = options
        return 0


def test_menu_shows_descriptions_and_passes_selected_operation(monkeypatch, capsys) -> None:
    answers = iter(["1", "status"])
    manager = StubManager()
    runtime = FakeRuntime(FakeSystem(), language="ru")

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = MenuInterface(manager=manager, runtime=runtime).run()
    captured = capsys.readouterr().out

    assert result == 0
    assert "Примеры:" in captured
    assert "mknight --all --activate" in captured
    assert "Доступные модули:" in captured
    assert "1) Firewall" in captured
    assert "Настраивает UFW" in captured
    assert "Доступные действия:" in captured
    assert "status: Показать текущее состояние без внесения изменений." in captured
    assert "Обслуживание утилиты:" in captured
    assert "9) update" in captured
    assert "10) reinstall" in captured
    assert "11) remove" in captured
    assert "Подсказка:" in captured
    assert manager.last_options is not None
    assert manager.last_options.service_codes == [1]
    assert manager.last_options.operation.value == "status"


def test_menu_runs_update_maintenance_action(monkeypatch, capsys) -> None:
    answers = iter(["9"])
    manager = StubManager()
    runtime = FakeRuntime(FakeSystem(), language="ru")
    called: dict[str, object] = {}

    def fake_run(command, check, env):
        called["command"] = command
        called["check"] = check
        called["env"] = env
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("subprocess.run", fake_run)

    result = MenuInterface(manager=manager, runtime=runtime).run()
    captured = capsys.readouterr().out

    assert result == 0
    assert called["command"] == ["bash", str(Path("D:/Projects/meowned_knight/install.sh"))]
    assert called["check"] is False
    assert called["env"]["MKNIGHT_INSTALL_DIR"] == str(Path("D:/Projects/meowned_knight"))
    assert "Выбрано действие обслуживания: update." in captured
    assert "Действие обслуживания завершено успешно." in captured


def test_menu_requires_confirmation_before_remove(monkeypatch, capsys) -> None:
    answers = iter(["11", "nope"])
    manager = StubManager()
    runtime = FakeRuntime(FakeSystem(), language="ru")

    def fail_run(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called when removal is cancelled")

    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("subprocess.run", fail_run)

    result = MenuInterface(manager=manager, runtime=runtime).run()
    captured = capsys.readouterr().out

    assert result == 0
    assert "Удаление отменено." in captured
