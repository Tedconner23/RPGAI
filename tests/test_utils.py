from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rpg_ai.utils import load_source_files, upload_source_files


class DummyClient:
    def __init__(self) -> None:
        self.names: list[str] = []

    class _Files:
        def __init__(self, outer: 'DummyClient') -> None:
            self.outer = outer

        def create(self, file, purpose: str):  # pragma: no cover - simple stub
            name = Path(file.name).name
            self.outer.names.append(name)
            return type('Uploaded', (), {'id': f'id_{name}'})

    @property
    def files(self):  # pragma: no cover - simple stub
        return DummyClient._Files(self)


def test_load_source_files_recurses_and_reads_cs(tmp_path: Path) -> None:
    (tmp_path / 'a.txt').write_text('alpha', encoding='utf-8')
    sub = tmp_path / 'nested'
    sub.mkdir()
    (sub / 'b.cs').write_text('class B {}', encoding='utf-8')
    (sub / 'ignore.md').write_text('nope', encoding='utf-8')

    text = load_source_files(tmp_path)
    assert 'File: a.txt' in text
    assert 'alpha' in text
    assert 'File: nested/b.cs' in text
    assert 'class B' in text
    assert 'ignore.md' not in text


def test_upload_source_files_recurses_and_includes_cs(tmp_path: Path) -> None:
    (tmp_path / 'one.txt').write_text('1', encoding='utf-8')
    sub = tmp_path / 'nested'
    sub.mkdir()
    (sub / 'two.cs').write_text('2', encoding='utf-8')
    (tmp_path / 'ignore.md').write_text('no', encoding='utf-8')

    client = DummyClient()
    ids = upload_source_files(client, tmp_path)

    assert set(ids) == {'id_one.txt', 'id_two.cs'}
    assert set(client.names) == {'one.txt', 'two.cs'}
