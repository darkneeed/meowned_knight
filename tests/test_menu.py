from __future__ import annotations

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
    assert "Подсказка:" in captured
    assert manager.last_options is not None
    assert manager.last_options.service_codes == [1]
    assert manager.last_options.operation.value == "status"
