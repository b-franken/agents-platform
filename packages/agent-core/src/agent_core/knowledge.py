"""Knowledge base manager — upload documents to a vector store.

Usage:
    uv run python -m agent_core.knowledge upload
    uv run python -m agent_core.knowledge status
    uv run python -m agent_core.knowledge delete
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from openai import APIError, AsyncOpenAI

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from dotenv import load_dotenv

from .factory import create_client

__all__: list[str] = []

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".md",
        ".txt",
        ".html",
        ".htm",
        ".docx",
        ".doc",
        ".csv",
        ".json",
    }
)


def _find_knowledge_dir() -> Path:
    return Path.cwd() / "knowledge"


def _get_documents(knowledge_dir: Path) -> list[Path]:
    if not knowledge_dir.exists():
        return []
    return sorted(
        p
        for p in knowledge_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
        and p.name != ".gitkeep"
    )


async def _upload_files(openai_client: AsyncOpenAI, docs: list[Path]) -> list[str]:
    file_ids: list[str] = []
    for doc in docs:
        print(f"  Uploading: {doc.name}...", end=" ")
        try:
            with doc.open("rb") as f:
                uploaded = await openai_client.files.create(
                    file=f,
                    purpose="user_data",
                )
            file_ids.append(uploaded.id)
            print(f"OK ({uploaded.id})")
        except OSError:
            logger.exception("Upload failed for %s", doc.name)
            print("FAILED")
    return file_ids


async def _create_store(openai_client: AsyncOpenAI, name: str) -> str | None:
    try:
        vs = await openai_client.vector_stores.create(
            name=name,
            expires_after={"anchor": "last_active_at", "days": 30},
        )
        return vs.id
    except APIError:
        logger.exception("Vector store creation failed")
        return None


async def _add_files(
    openai_client: AsyncOpenAI,
    store_id: str,
    file_ids: list[str],
) -> int:
    failed = 0
    for fid in file_ids:
        try:
            result = await openai_client.vector_stores.files.create_and_poll(
                vector_store_id=store_id,
                file_id=fid,
            )
            if result.last_error is not None:
                logger.error(
                    "Processing failed for %s: %s",
                    fid,
                    result.last_error.message,
                )
                failed += 1
            else:
                print(f"  File {fid} processed")
        except APIError:
            logger.exception("Error adding %s to store", fid)
            failed += 1
    return failed


async def _cleanup_files(openai_client: AsyncOpenAI, file_ids: list[str]) -> None:
    for fid in file_ids:
        try:
            await openai_client.files.delete(fid)
        except APIError:
            logger.debug("Could not clean up file %s", fid)


async def upload() -> None:
    """Upload documents from knowledge/ to a vector store."""
    knowledge_dir = _find_knowledge_dir()
    docs = _get_documents(knowledge_dir)
    if not docs:
        print(f"No documents found in {knowledge_dir}")
        return

    print(f"Found {len(docs)} document(s)")
    client = create_client()
    oc = client.client
    if oc is None:
        print("Could not initialize OpenAI client")
        return

    file_ids = await _upload_files(oc, docs)
    if not file_ids:
        return

    print("Creating vector store...", end=" ")
    store_id = await _create_store(oc, f"knowledge-{Path.cwd().name}")
    if not store_id:
        print("FAILED")
        await _cleanup_files(oc, file_ids)
        return
    print(f"OK ({store_id})")

    failed = await _add_files(oc, store_id, file_ids)
    if failed:
        print(f"{failed} file(s) failed")

    print(f"\nVector store ready: {store_id}")
    print(f"Add to .env: VECTOR_STORE_ID={store_id}")


async def status() -> None:
    """Show vector store status."""
    vs_id = os.getenv("VECTOR_STORE_ID")
    if not vs_id:
        print("No VECTOR_STORE_ID in .env")
        return
    oc = create_client().client
    if oc is None:
        print("Could not initialize OpenAI client")
        return
    try:
        vs = await oc.vector_stores.retrieve(vs_id)
        print(f"Vector Store: {vs.name} ({vs.id})")
        print(f"  Status: {vs.status}")
        completed = vs.file_counts.completed
        in_progress = vs.file_counts.in_progress
        print(f"  Files: {completed} processed, {in_progress} in progress")
    except APIError:
        logger.exception("Could not retrieve vector store %s", vs_id)


async def delete() -> None:
    """Delete vector store and files."""
    vs_id = os.getenv("VECTOR_STORE_ID")
    if not vs_id:
        print("No VECTOR_STORE_ID in .env")
        return
    oc = create_client().client
    if oc is None:
        print("Could not initialize OpenAI client")
        return
    try:
        files = await oc.vector_stores.files.list(vs_id)
        async for ref in files:
            try:
                await oc.files.delete(ref.id)
                print(f"  Deleted file {ref.id}")
            except APIError:
                logger.warning("Could not delete file %s", ref.id)
        await oc.vector_stores.delete(vs_id)
        print(f"Vector store {vs_id} deleted. Remove VECTOR_STORE_ID from .env.")
    except APIError:
        logger.exception("Error deleting vector store %s", vs_id)


COMMANDS: dict[str, Callable[[], Awaitable[None]]] = {
    "upload": upload,
    "status": status,
    "delete": delete,
}


async def main() -> None:
    load_dotenv()
    log_fmt = "%(asctime)s | %(levelname)s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python -m agent_core.knowledge [{' | '.join(COMMANDS)}]")
        return
    await COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    asyncio.run(main())
