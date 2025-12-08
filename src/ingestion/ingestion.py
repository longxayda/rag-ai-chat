import loader
import chunker
import json
import embedder
import indexer
from pathlib import Path


processed_dir = Path.cwd() / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)
processed_file_path = processed_dir / "chunks.json"
processed_doc_path = processed_dir / "pages.json"


if __name__ == "__main__":
    
    print("Retrieving files...")
    files = loader.retrieve_files_from('./data/raw')
    
    print("Process docs parallel... ")
    docs = loader.process_files_concurrently(files, max_workers=4)

    print("Load pages to json file...")
    with processed_doc_path.open('w', encoding='utf-8') as file:
        json.dump(docs, file, indent=4, ensure_ascii=True)
    
    print("Chunking docs...")
    chunked_docs = chunker.process_chunks_concurrently(docs, max_workers=4)

    print("Load chunks to json file...")
    with processed_file_path.open('w', encoding='utf-8') as file:
        json.dump(chunked_docs, file, indent=4, ensure_ascii=True)

    print("Creating embeddings from chunks...")
    chunks, embeddings = embedder.get_embeddings(processed_file_path=processed_file_path)

    print("Create table if not exist...")
    indexer.init_db()
    
    print("Insert embeddings & related info to Postgres...")
    indexer.insert_embeddings(chunks=chunks, embeddings=embeddings)

    print("Done ingestion")