import hashlib
from pathlib import Path


def compute_file_hash(path: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_paths_hash(paths: list[Path]) -> str:
    """Hash нескольких файлов. Учитывает имя и содержимое. Только файлы."""
    sha256 = hashlib.sha256()
    for p in sorted(paths, key=lambda x: x.name):
        if not p.is_file():
            continue
        sha256.update(p.name.encode("utf-8"))
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
    return sha256.hexdigest()
