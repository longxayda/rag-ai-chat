# loader.py
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from pypdf import PdfReader


# ------------------------
# Base Loader
# ------------------------

class BaseLoader(ABC):
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path
        self.metadata: dict[str, Any] = {}
        self.text: str = ""

    @abstractmethod
    def load(self) -> None:
        pass

    def extract_metadata(self):
        self.metadata = {
            "file_name": self.file_path.name,
            "file_path": str(self.file_path.resolve()),
            "file_size": os.path.getsize(self.file_path),
            "file_type": self.file_path.suffix.lower()
        }

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.file_path.stem,
            "title": self.file_path.stem,
            "path": str(self.file_path.resolve()),
            "text": self.text,
            "metadata": self.metadata
        }


# ------------------------
# PDF Loader (no pages, no images)
# ------------------------

class PdfLoader(BaseLoader):
    def load(self) -> None:
        print("Using PDF Loader...")
        try:
            reader = PdfReader(self.file_path)
            texts: List[str] = []

            for page in reader.pages:
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""

                if page_text.strip():
                    texts.append(page_text.strip())

            # 🔹 Merge all pages into ONE document
            self.text = "\n\n".join(texts)

        except Exception as e:
            print(f"❌ Failed to load PDF {self.file_path}: {e}")
            self.text = ""


# ------------------------
# TXT / MD Loader
# ------------------------

class TxtLoader(BaseLoader):
    def load(self) -> None:
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            self.text = f.read()


# ------------------------
# HTML Loader (strip tags)
# ------------------------

class HtmlLoader(BaseLoader):
    def load(self) -> None:
        # with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
        #     soup = BeautifulSoup(f.read(), "html.parser")
        #     self.text = soup.get_text(separator="\n")
        pass


# ------------------------
# Null Loader
# ------------------------

class NullLoader(BaseLoader):
    def load(self) -> None:
        self.text = ""


# ------------------------
# Loader selector
# ------------------------

def get_loader(file_path: Path) -> BaseLoader:
    ext = file_path.suffix.lower()

    if file_path.name == ".gitkeep":
        return NullLoader(file_path)

    if ext == ".pdf":
        return PdfLoader(file_path)
    elif ext in [".txt", ".md"]:
        return TxtLoader(file_path)
    elif ext in [".html", ".htm"]:
        return HtmlLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ------------------------
# File retrieval helpers
# ------------------------

def retrieve_files_from(directory: str) -> list[Path]:
    p = Path(directory)
    if not p.exists() or not p.is_dir():
        return []
    return sorted([f for f in p.iterdir() if f.is_file()])


# ------------------------
# Process ONE file → ONE document
# ------------------------

def process_file(file_path: Path) -> dict[str, Any]:
    try:
        loader = get_loader(file_path)
        loader.load()
        loader.extract_metadata()
        return loader.to_document()

    except Exception as e:
        print(f"❌ Error processing file {file_path}: {e}")
        return {
            "id": f"{file_path.stem}_error",
            "title": file_path.stem,
            "text": "",
            "metadata": {
                "file_path": str(file_path),
                "error": str(e)
            }
        }


# ------------------------
# Concurrent processing
# ------------------------

def process_files_concurrently(
    files: list[Path],
    max_workers: int = 4
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, f) for f in files]
        for future in as_completed(futures):
            documents.append(future.result())

    return documents
