# split the documents into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor, as_completed

class Chunker():
    def __init__(self, doc):
        self.doc = doc
        self.chunks = []
        self.chunked_doc = []
        self.chunk_size: int = 1000
        self.chunk_overlap: int = 200

    def chunk(self):
        """
        Perform fixed sized chunking
        """
        print("Using Chunker...")
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap)
        
        # Split the text into chunks
        self.chunks = text_splitter.split_text(self.doc['text'])
    
    def to_chunked_doc(self):
        """
        Return chunked doc with metadata
        """
        for index, content in enumerate(self.chunks):
            chunk = {
                "id": f"{self.doc.get('id')}_chunk_{index}",
                "chunk_index": index,
                "text": content,
                "metadata": self.doc.get('metadata', {}).copy(),
            }
            self.chunked_doc.append(chunk)
        return self.chunked_doc

def process_chunk(doc):
    """
    Process 1 chunker
    """
    chunker = Chunker(doc=doc)
    chunker.chunk()
    chunked_doc = chunker.to_chunked_doc()
    return chunked_doc

def process_chunks_concurrently(docs: list, max_workers=4) -> list:
    """
    Process many Chunkers
    """
    chunked_docs = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, doc) for doc in docs]
        for future in as_completed(futures):
            for chunk in future.result():
                chunked_docs.append(chunk)
    return chunked_docs