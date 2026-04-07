import json
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parents[2]
CHUNK_DIR = BASE_DIR / "data" / "chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)


def save_chunks(document_id: str, chunks: List[Dict]) -> None:
    file_path = CHUNK_DIR / f"{document_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            {"document_id": document_id, "chunks": chunks},
            f,
            indent=2,
            ensure_ascii=False
        )


def load_chunks(document_id: str) -> List[Dict]:
    file_path = CHUNK_DIR / f"{document_id}.json"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f).get("chunks", [])
