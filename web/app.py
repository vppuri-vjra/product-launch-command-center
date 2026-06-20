"""
FastAPI backend for the Product Launch Command Center web interface.
Serves the single-page app and provides a streaming chat endpoint.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import CommandCenter

app = FastAPI(title="Project Nightingale Launch Command Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store: session_id → CommandCenter
sessions: dict[str, CommandCenter] = {}


def get_session(session_id: str) -> CommandCenter:
    if session_id not in sessions:
        sessions[session_id] = CommandCenter()
    return sessions[session_id]


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path) as f:
        return f.read()


@app.post("/api/greet")
async def greet(body: dict):
    session_id = body.get("session_id", "default")
    center = get_session(session_id)
    if not center.started:
        greeting = center.greet()
    else:
        greeting = "Welcome back to the Project Nightingale Launch Command Center. What do you need?"
    return {"text": greeting, "agent": "greeter"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    center = get_session(req.session_id)
    response, done = center.chat(req.message)
    return {
        "text": response,
        "agent": center.current_agent,
        "done": done,
    }


@app.delete("/api/session/{session_id}")
async def reset_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "reset"}


@app.get("/health")
async def health():
    return {"status": "ok"}
