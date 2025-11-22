from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag.scripts import cli
from rag.service import SearchHit


class DummyService:
    def __init__(self) -> None:
        self.ingest_calls: list[tuple[list[Path], dict | None]] = []
        self.search_calls: list[tuple[str, int | None]] = []
        self.ingest_return: list[str] = ["doc-1"]
        self.search_return: list[SearchHit] = []

    def ingest_files(self, paths, metadata=None):
        self.ingest_calls.append((list(paths), metadata))
        return self.ingest_return

    def search(self, query, limit=None):
        self.search_calls.append((query, limit))
        return self.search_return


def test_cli_ingest_calls_service(tmp_path, capsys):
    svc = DummyService()
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello")

    exit_code = cli.run(["ingest", str(file_path), "-m", "team=ml", "-m", "source=test"], service=svc)

    assert exit_code == 0
    assert len(svc.ingest_calls) == 1
    paths, metadata = svc.ingest_calls[0]
    assert paths[0] == file_path.resolve()
    assert metadata == {"team": "ml", "source": "test"}

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"document_ids": ["doc-1"]}


def test_cli_ingest_invalid_metadata_raises(tmp_path):
    svc = DummyService()
    file_path = tmp_path / "note.txt"
    file_path.write_text("content")

    with pytest.raises(SystemExit) as exc:
        cli.run(["ingest", str(file_path), "-m", "broken"], service=svc)

    assert "Invalid metadata entry" in str(exc.value)


def test_cli_search_outputs_hits(capsys):
    svc = DummyService()
    svc.search_return = [
        SearchHit(
            chunk_id="chunk-5",
            document_id="doc-5",
            text="chunk text",
            score=0.78,
            metadata={"origin": "cli"},
        )
    ]

    exit_code = cli.run(["search", "test", "-l", "1"], service=svc)

    assert exit_code == 0
    assert svc.search_calls == [("test", 1)]
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "hits": [
            {
                "chunk_id": "chunk-5",
                "document_id": "doc-5",
                "text": "chunk text",
                "score": 0.78,
                "metadata": {"origin": "cli"},
            }
        ]
    }
