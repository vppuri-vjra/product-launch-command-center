#!/usr/bin/env python3
"""
Ingest Product Launch Command Center KB files into Pinecone.

Reads the 3 KB files from knowledge_base/, chunks them, embeds with
OpenAI text-embedding-3-small, and upserts into Pinecone.

Index:     nightingale-launch
Namespaces: technical, gtm, launch
Embedding:  text-embedding-3-small (1536-dim)
Chunking:   512 tokens (~2048 chars), 64 token overlap (~256 chars)

Usage:
    python scripts/ingest_pinecone.py

Requires .env with:
    OPENAI_API_KEY
    PINECONE_API_KEY
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = 2048
CHUNK_OVERLAP = 256
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
INDEX_NAME = "nightingale-launch"
BATCH_SIZE = 50

ROOT = Path(__file__).parent.parent
KB_DIR = ROOT / "knowledge_base"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

KB_FILES = [
    {
        "file": "KB_Technical_Readiness.txt",
        "doc_id": "kb-technical-readiness",
        "namespace": "technical",
        "title": "Technical Readiness KB",
    },
    {
        "file": "KB_GTM_Marketing.txt",
        "doc_id": "kb-gtm-marketing",
        "namespace": "gtm",
        "title": "GTM & Marketing KB",
    },
    {
        "file": "KB_Launch_Plan.txt",
        "doc_id": "kb-launch-plan",
        "namespace": "launch",
        "title": "Launch Plan KB",
    },
]

oai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = oai.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend([d.embedding for d in resp.data])
    return embeddings


def ingest():
    index = pc.Index(INDEX_NAME)
    manifest = {
        "index": INDEX_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIM,
        "chunk_size_chars": CHUNK_SIZE,
        "chunk_overlap_chars": CHUNK_OVERLAP,
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "documents": [],
    }

    for kb in KB_FILES:
        filepath = KB_DIR / kb["file"]
        print(f"\n=== {kb['title']} ({kb['file']}) ===")

        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        print(f"  {len(chunks)} chunks ({len(text)} chars)")

        # Delete existing vectors for this doc_id (idempotent)
        ns = kb["namespace"]
        existing_ids = []
        try:
            for ids in index.list(namespace=ns, prefix=kb["doc_id"]):
                existing_ids.extend(ids)
            if existing_ids:
                index.delete(ids=existing_ids, namespace=ns)
                print(f"  Deleted {len(existing_ids)} existing vectors")
        except Exception:
            pass

        # Embed
        print(f"  Embedding {len(chunks)} chunks...")
        embeddings = embed_texts(chunks)

        # Upsert
        vectors = []
        vector_ids = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vid = f"{kb['doc_id']}-chunk{i}"
            vector_ids.append(vid)
            vectors.append({
                "id": vid,
                "values": emb,
                "metadata": {
                    "title": kb["title"],
                    "source": kb["file"],
                    "chunk_index": i,
                    "text": chunk[:1000],
                },
            })

        # Upsert in batches
        for i in range(0, len(vectors), BATCH_SIZE):
            batch = vectors[i : i + BATCH_SIZE]
            index.upsert(vectors=batch, namespace=ns)

        print(f"  Upserted {len(vectors)} vectors to namespace '{ns}'")

        manifest["documents"].append({
            "doc_id": kb["doc_id"],
            "title": kb["title"],
            "file": kb["file"],
            "namespace": ns,
            "chunk_count": len(chunks),
            "vector_ids": vector_ids,
        })

    # Write manifest
    manifest_path = OUTPUT_DIR / "pinecone_ingestion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n✅ Manifest written to {manifest_path}")

    total = sum(d["chunk_count"] for d in manifest["documents"])
    print(f"✅ Total: {total} vectors across {len(manifest['documents'])} documents")


if __name__ == "__main__":
    ingest()
