from pathlib import Path
import logging
import asyncio
import uuid
import json


from . import loader
from .import embedder

from ..services import rag, task_logs
from ..core.database import AsyncDatabase
from ..core import database
from ..utils.file import compute_file_hash, clean_vietnamese_text
from . import chunker

from ..extraction.retriever import collect_heritage_chunks, collect_people_chunks
from ..extraction.extractor import extract_heritages_from_chunks, extract_people_from_chunks
from ..services.rag import insert_heritages, insert_people
from ..linking.engine import run_linking_engine

logger = logging.getLogger(__name__)



async def run_ingestion_pipeline(file_path: Path, doc_id: str):
    task_id = await task_logs.insert_task_log(doc_id=doc_id, initial_state="INITIALIZED")
    
    if not task_id:
        logger.error(f"Could not start pipeline for {doc_id} due to log insert failure.")
        return
    try:
        await task_logs.update_state(task_id, "LOADING")
        file = loader.retrieve_file_from(file_path)
        
        doc = loader.process_file(file_path=file)
        
        await task_logs.update_state(task_id, "CHUNKING")
        chunks_from_doc = chunker.process_chunk(doc=doc)

        await task_logs.update_state(task_id, "EMBEDDING")
        chunks, embeddings = embedder.get_embeddings(chunks_from_doc=chunks_from_doc)
        
        await task_logs.update_state(task_id, "INSERTING")
        async for conn in database.get_db_conn():
            try:
                file.insert_embeddings(conn=conn, chunks=chunks, embeddings=embeddings)
            except Exception as e:
                raise
            break
        
        await task_logs.update_state(task_id, "COMPLETED")
        logger.info("Done ingestion")
    except Exception as e:
        error_details = {"error_type": type(e).__name__, "message": str(e)}
        await task_logs.update_state(task_id, "FAILED", metadata=error_details)
        logger.exception(f"ERROR in ingestion pipeline for doc {doc_id}: {e}")
        
    finally:
        # Optional: Cleanup the raw file, regardless of success or failure
        try:
            file_path.unlink(missing_ok=True)
            logger.debug(f"Cleaned up file {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete raw file {file_path}: {e}")
            
            
async def run_heritage_pipeline(
    file_path: Path = Path.cwd() / "data" / "raw"
):
    processed_file_path = Path.cwd() / "data" / "processed"
    try:
        await AsyncDatabase.initialize()
    except Exception as e:
        logger.error(f"Failed to connect to DB: {e}")
        return

    try:
        documents = loader.retrieve_files_from(file_path)

        for document in documents:
            file_hash = compute_file_hash(document)

            async with AsyncDatabase.get_connection() as conn:
                # 1️⃣ Check dedup FIRST
                row = await conn.fetchrow(
                    "SELECT id FROM documents WHERE file_hash = $1",
                    file_hash
                )

                if row:
                    print(f"File already indexed {document.name}")

                    continue

                # 2️⃣ Create document_id
                document_id = uuid.uuid4()

                # 3️⃣ Insert document FIRST
                async with conn.transaction():
                    await rag.insert_document(
                        conn,
                        document_id,
                        document.name,
                        str(document),
                        file_hash
                    )

                    # 4️⃣ Process + chunk
                    document_obj = loader.process_file(document)
                    document_obj["text"] = clean_vietnamese_text(document_obj["text"])
                    
                    with open(processed_file_path / "pages.json", 'w', encoding='utf-8') as outfile:
                        json.dump(document_obj, outfile, indent=4, ensure_ascii=False)
                        
                    chunks = chunker.semantic_chunk_text(text=document_obj['text'])
                    
                    if not chunks:
                        continue
                    
                    chunk_docs = [
                        {
                            "id": f"{str(document_obj['id'])}_c{i}",
                            "document_id": str(document_id),
                            "chunk_index": i,
                            "text": chunk,
                            "metadata": document_obj["metadata"]
                        }
                        for i, chunk in enumerate(chunks)
                    ]
                    with open(processed_file_path / "chunks.json", 'w', encoding='utf-8') as outfile:
                        json.dump(chunk_docs, outfile, indent=4, ensure_ascii=False)


                    # 6️⃣ Embed AFTER dedup confirmed
                    chunks, embeddings = await embedder.get_embeddings(chunk_docs)

                    # 7️⃣ Insert embeddings
                    await rag.insert_embeddings(conn, chunks, embeddings)
                    print(f"Successfully indexed: {document.name}")
                    
                    # await process_heritage_extraction(conn, document_id)
                    # await process_people_extraction(conn, document_id)

                # try:
                #     await run_linking_engine(conn, document_id)
                # except Exception as e:
                #     logger.warning(f"Linking failed for {document_id}: {e}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

    finally:
        await AsyncDatabase.close()

async def process_heritage_extraction(conn, document_id):
    chunks = await collect_heritage_chunks(conn, document_id)

    if not chunks:
        print("ℹ️ No heritage-related chunks")
        return

    heritages = await extract_heritages_from_chunks(chunks)

    if not heritages:
        print("⚠️ No heritage extracted")
        return

    await insert_heritages(conn, document_id, heritages)

    print(f"✅ Inserted {len(heritages)} heritages")

async def process_people_extraction(conn, document_id):
    chunks = await collect_people_chunks(conn, document_id)

    if not chunks:
        print("ℹ️ No people-related chunks")
        return

    people = await extract_people_from_chunks(chunks)

    if not people:
        print("⚠️ No people extracted")
        return

    await insert_people(conn, document_id, people)

    print(f"✅ Inserted {len(people)} people")


if __name__ == "__main__":
    asyncio.run(run_heritage_pipeline())