#!/usr/bin/env python3
"""
Query the Product Launch Command Center Pinecone index.

Embeds a user question, retrieves top-k matching chunks from the
appropriate namespace(s), and generates an answer using Claude.

Usage:
    python scripts/query_pinecone.py "What is the deployment plan?"
    python scripts/query_pinecone.py --namespace technical "What's the QA status?"
    python scripts/query_pinecone.py --all "Give me an executive summary"

Requires .env with:
    OPENAI_API_KEY
    PINECONE_API_KEY
    ANTHROPIC_API_KEY
"""

import os
import sys
import argparse
from pathlib import Path

from openai import OpenAI
from pinecone import Pinecone
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = "nightingale-launch"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5

NAMESPACES = {
    "technical": "Technical Readiness",
    "gtm": "GTM & Marketing",
    "launch": "Launch Plan",
}

oai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
claude = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def embed_query(query: str) -> list[float]:
    resp = oai.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    return resp.data[0].embedding


def retrieve(query: str, namespaces: list[str], top_k: int = TOP_K) -> list[dict]:
    index = pc.Index(INDEX_NAME)
    embedding = embed_query(query)

    all_matches = []
    for ns in namespaces:
        results = index.query(
            vector=embedding,
            top_k=top_k,
            namespace=ns,
            include_metadata=True,
        )
        for match in results.matches:
            all_matches.append({
                "id": match.id,
                "score": match.score,
                "namespace": ns,
                "title": match.metadata.get("title", ""),
                "text": match.metadata.get("text", ""),
            })

    # Dedup by id, keep highest score
    seen = {}
    for m in all_matches:
        if m["id"] not in seen or m["score"] > seen[m["id"]]["score"]:
            seen[m["id"]] = m

    return sorted(seen.values(), key=lambda x: x["score"], reverse=True)


def generate_answer(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source: {c['title']} ({c['namespace']})]\n{c['text']}"
        for c in chunks[:10]
    )

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=f"""You are a specialist for the Project Nightingale Launch Command Center.
Answer the user's question using ONLY the retrieved context below.
Cite specific data points. If information is not available, say so.

## Retrieved Context
{context}""",
        messages=[{"role": "user", "content": query}],
    )
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Query Nightingale Pinecone index")
    parser.add_argument("query", help="The question to ask")
    parser.add_argument("--namespace", "-n", choices=list(NAMESPACES.keys()),
                        help="Query a specific namespace")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Query all namespaces")
    parser.add_argument("--top-k", "-k", type=int, default=TOP_K,
                        help=f"Number of results per namespace (default: {TOP_K})")
    parser.add_argument("--raw", action="store_true",
                        help="Show raw retrieved chunks without Claude synthesis")
    args = parser.parse_args()

    if args.namespace:
        ns_list = [args.namespace]
    elif args.all:
        ns_list = list(NAMESPACES.keys())
    else:
        ns_list = list(NAMESPACES.keys())

    print(f"\n🔍 Query: {args.query}")
    print(f"📂 Namespaces: {', '.join(ns_list)}")
    print(f"🎯 Top-K: {args.top_k}\n")

    chunks = retrieve(args.query, ns_list, args.top_k)
    print(f"Retrieved {len(chunks)} chunks:\n")

    for i, c in enumerate(chunks[:10]):
        print(f"  [{i+1}] (score: {c['score']:.4f}) {c['title']} [{c['namespace']}]")
        if args.raw:
            print(f"      {c['text'][:200]}...")
        print()

    if not args.raw:
        print("─" * 60)
        print("🤖 Claude Answer:\n")
        answer = generate_answer(args.query, chunks)
        print(answer)
        print()


if __name__ == "__main__":
    main()
