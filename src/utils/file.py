import hashlib
from pathlib import Path
import re

def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_vietnamese_text(text: str) -> str:
    # Remove space between split characters
    text = re.sub(r'(?<=\b\w)\s+(?=\w\b)', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()