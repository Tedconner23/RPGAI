from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rpg_ai.memory import update_conversation_summary, update_user_preferences


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.output_text = text


class DummyClient:
    def __init__(self, text: str, fail: bool = False) -> None:
        self._text = text
        self._fail = fail

    class _Responses:
        def __init__(self, outer: 'DummyClient') -> None:
            self.outer = outer

        def create(self, model: str, input: str):  # pragma: no cover - simple stub
            if self.outer._fail:
                raise RuntimeError("fail")
            return DummyResponse(self.outer._text)

    @property
    def responses(self):  # pragma: no cover - simple stub
        return DummyClient._Responses(self)


def test_update_conversation_summary(tmp_path: Path) -> None:
    client = DummyClient("summary")
    history = [{"role": "user", "content": "hello"}]
    path = tmp_path / "summary.txt"
    update_conversation_summary(client, history, path)
    assert path.read_text() == "summary"


def test_update_user_preferences(tmp_path: Path) -> None:
    client = DummyClient("prefs")
    history = [{"role": "assistant", "content": "hi"}]
    path = tmp_path / "prefs.txt"
    update_user_preferences(client, history, path)
    assert path.read_text() == "prefs"


def test_failed_summarization_keeps_file(tmp_path: Path) -> None:
    client = DummyClient("irrelevant", fail=True)
    path = tmp_path / "keep.txt"
    path.write_text("existing")
    update_conversation_summary(client, [], path)
    assert path.read_text() == "existing"
