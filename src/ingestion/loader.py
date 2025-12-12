import os
from abc import ABC, abstractmethod
from pypdf import PdfReader
from pathlib import Path
from typing import List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

def retrieve_files_from(directory: str) -> list[Path]:
    """
    Return files from a directory
    """
    p = Path(directory)
    if not p.exists() or not p.is_dir():
        return []
    files = [file for file in sorted(p.iterdir()) if file.is_file()]
    return files

class BaseLoader(ABC):
    """
    Base loader that declares attributes of each document
        - file path
        - pages 
        - metadata (name, path, size, type)
    """
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.metadata: dict[str, Any] = {}
        self.pages: list[str] = []

    @abstractmethod
    def load(self):
        pass
              
    def extract_metadata(self):
        self.metadata = {
            "file_name": os.path.basename(self.file_path),
            "file_path": str(self.file_path),
            "file_size": os.path.getsize(self.file_path),
            "file_type": os.path.splitext(self.file_path)[1].lower()
        }
    
    def to_document(self, page: str, page_index: int) -> dict[str, Any]:
        return {
            "id": f"{self.file_path.stem}_page_{page_index}",
            "page_index": page_index,
            "path": str(self.file_path.resolve()),
            "title": self.file_path.stem,
            "text": page,
            "metadata": self.metadata
        }

class TxtLoader(BaseLoader):
    pass

class HtmlLoader(BaseLoader):
    pass

class NullLoader(BaseLoader):
    def load(self) -> list:
        return []

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
                if page_text:
                    texts.append(page_text)
            self.pages = texts
        except Exception:
            self.pages = []


def get_loader(file_path: Path) -> BaseLoader:
    """
    Choose approriate Loader based on file extension (.pdf, .html, .txt, ...)
    """
    ext = os.path.splitext(file_path)[1].lower()
    if os.path.basename(file_path) == ".gitkeep":
        return NullLoader(file_path)
    if ext == ".pdf":
        return PdfLoader(file_path)
    elif ext in [".txt", ".md"]:
        return TxtLoader(file_path)
    elif ext in [".html", ".htm"]:
        return HtmlLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
        
def process_file(file_path: Path) -> list[dict] | dict[str, Any]:
    """
    Single file processing (1 Loader):
      - load
      - extract metadata
      - return document dict
    """
    loader = get_loader(file_path=file_path)
    file_pages = []
    try:
        loader.load()   # get pages attribute
        pages: list[str] = loader.pages
        for page_index, page in enumerate(pages):
            loader.extract_metadata()
            file_pages.append(loader.to_document(page=page, page_index=page_index))
        return file_pages # [{},{},{}]
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return {"text": "", "metadata": {"file_path": file_path, "error": str(e)}}

def process_files_concurrently(files: list[Path], max_workers: int = 4) -> list:
    """
    Process many Loaders on many threads
    """
    documents: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, file) for file in files]
        for future in as_completed(futures):
            for page in future.result():
                documents.append(page)
    return documents