from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:  # Optional heavy deps guarded to keep CLI responsive
    import docx  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docx = None

try:
    from pptx import Presentation  # type: ignore
except Exception:  # pragma: no cover
    Presentation = None

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None


@dataclass
class RawDocument:
    text: str
    metadata: dict


SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".pdf", ".docx", ".pptx"}


def load_path(path: Path) -> list[RawDocument]:
    if path.is_dir():
        documents: list[RawDocument] = []
        for file in sorted(path.rglob("*")):
            if file.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.extend(_load_file(file))
        return documents
    return _load_file(path)


def _load_file(path: Path) -> list[RawDocument]:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    metadata = {"source_path": str(path), "name": path.name}
    if suffix in {".txt", ".md"}:
        return [RawDocument(text=path.read_text(encoding="utf-8"), metadata=metadata)]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data.get("text") or json.dumps(data, ensure_ascii=False)
        return [RawDocument(text=text, metadata={**metadata, "kind": "json"})]
    if suffix == ".pdf":
        if PdfReader is None:
            raise RuntimeError("pypdf is required to read PDF files")
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return [RawDocument(text=text, metadata={**metadata, "kind": "pdf"})]
    if suffix == ".docx":
        if docx is None:
            raise RuntimeError("python-docx is required to read DOCX files")
        document = docx.Document(str(path))
        text = "\n".join(p.text for p in document.paragraphs)
        return [RawDocument(text=text, metadata={**metadata, "kind": "docx"})]
    if suffix == ".pptx":
        if Presentation is None:
            raise RuntimeError("python-pptx is required to read PPTX files")
        prs = Presentation(str(path))
        slides: Iterable[str] = (
            "\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text"))
            for slide in prs.slides
        )
        text = "\n".join(slides)
        return [RawDocument(text=text, metadata={**metadata, "kind": "pptx"})]
    raise ValueError(f"Unsupported file type: {path.suffix}")
