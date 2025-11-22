from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    clean_text = " ".join(text.split())
    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(clean_text):
        end = min(len(clean_text), start + chunk_size)
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(index=index, content=chunk))
            index += 1
        start = end - overlap
        if start < 0:
            start = 0
        if end == len(clean_text):
            break
    if not chunks and clean_text:
        chunks.append(TextChunk(index=0, content=clean_text))
    return chunks
