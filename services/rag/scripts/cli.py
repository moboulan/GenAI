from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence

from rag.service import RagService, SearchHit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag-cli", description="Utility commands for the RAG service")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest one or more files or directories")
    ingest.add_argument("paths", nargs="+", help="Files or directories to ingest")
    ingest.add_argument(
        "-m",
        "--metadata",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Document-level metadata key/value to attach (can be repeated)",
    )

    search = sub.add_parser("search", help="Search indexed chunks")
    search.add_argument("query", help="Natural language query to embed")
    search.add_argument("-l", "--limit", type=int, default=None, help="Max number of hits to return")

    return parser


def run(argv: Sequence[str] | None = None, service: RagService | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    svc = service or RagService.from_settings()

    if args.command == "ingest":
        return _run_ingest(args.paths, args.metadata, svc)
    if args.command == "search":
        return _run_search(args.query, args.limit, svc)
    parser.error("Unknown command")
    return 1


def _run_ingest(paths: Sequence[str], metadata_pairs: Iterable[str], service: RagService) -> int:
    metadata = _parse_metadata(metadata_pairs)
    resolved = [Path(p).resolve() for p in paths]
    ids = service.ingest_files(resolved, metadata or None)
    payload = {"document_ids": ids}
    print(json.dumps(payload, indent=2))
    return 0


def _run_search(query: str, limit: int | None, service: RagService) -> int:
    hits = service.search(query, limit=limit)
    payload = {"hits": [_serialize_hit(hit) for hit in hits]}
    print(json.dumps(payload, indent=2))
    return 0


def _serialize_hit(hit: SearchHit) -> dict:
    return {
        "chunk_id": hit.chunk_id,
        "document_id": hit.document_id,
        "text": hit.text,
        "score": hit.score,
        "metadata": hit.metadata,
    }


def _parse_metadata(pairs: Iterable[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Invalid metadata entry '{pair}', expected KEY=VALUE format")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit("Metadata keys cannot be empty")
        metadata[key] = value.strip()
    return metadata


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
