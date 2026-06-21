# Project Nightingale — System Architecture

## Overview

Project Nightingale is a **multi-agent voice + text AI Launch Command Center** built as a single static HTML file hosted on GitHub Pages. There is no backend server — the Claude API is called directly from the browser.

---

## System Layers

### 1. User Input
- **Voice** — Web Speech API (SpeechRecognition) for real-time speech-to-text
- **Text** — Chat input field with auto-resize
- **TTS Output** — SpeechSynthesis API, Daniel voice, rate 0.92, pitch 0.88

### 2. Orchestration — Greeter Agent
- Entry point for every conversation
- Classifies user intent from the first message
- Emits a `ROUTE:` signal in its response to hand off to the right specialist
- Runs on **claude-sonnet-4-6** via Anthropic API (direct browser access header)

**Routing logic:**
| User asks about | Routes to |
|---|---|
| Engineering, QA, deployment, rollback | Technical Readiness |
| Campaigns, press, sales, competitive | GTM & Marketing |
| Status overview, budget, risks, milestones | Executive Briefing |

### 3. Specialist Agents

| Agent | Color | Scope |
|---|---|---|
| **Technical Readiness** (T) | Green `#2d6a4f` | Sprint status, QA, API performance, deployment plan, on-call, rollback criteria |
| **GTM & Marketing** (M) | Amber `#b45309` | Campaign channels, key messaging, press embargo, sales enablement, competitive landscape |
| **Executive Briefing** (E) | Purple `#6d28d9` | High-level status, risks, budget summary, milestones, stakeholders — full KB access |

**Cross-routing:** Specialists can also route to each other mid-conversation via the same `ROUTE:` signal pattern.

### 4. Knowledge Base Scoping

Three KB files are embedded as JavaScript string constants in `launch.html`. Each agent only receives the files relevant to its domain — preventing information leakage across roles.

| KB File | Agents with Access | Contents |
|---|---|---|
| `KB_TECHNICAL` | Technical | Sprint status, QA results, API perf, deployment plan, rollback criteria, on-call schedule |
| `KB_GTM` | GTM & Marketing | Channel strategy, messaging, budget breakdown, competitive analysis, sales objection handling |
| `KB_LAUNCH` | Executive (+ all 3) | Launch overview, stakeholders, success metrics, risk register, budget summary, post-launch plan |

### 5. Vector Store — Pinecone

| Parameter | Value |
|---|---|
| Provider | Pinecone (production) · ChromaDB (local dev) |
| Index name | `nightingale-launch` |
| Namespaces | `technical` · `gtm` · `launch` |
| Embedding model | `text-embedding-3-small` |
| Dimensions | 1536 |
| Similarity metric | Cosine |
| Chunk size | 512 tokens |
| Chunk overlap | 64 tokens |
| Chunking strategy | Recursive text splitter |
| Top-k retrieval | 5 |

**Why `text-embedding-3-small`:**  
62M parameters · 5× cheaper than `text-embedding-3-large` · retrieval quality on par for short structured KB docs · low latency for real-time routing use case.

### 6. Infrastructure

| Component | Detail |
|---|---|
| **Hosting** | GitHub Pages — static, no backend, CDN cache (`max-age=600`) |
| **LLM API** | Anthropic Claude API (`claude-sonnet-4-6`) with `anthropic-dangerous-direct-browser-access: true` header |
| **API key storage** | `sessionStorage` — scoped to browser tab, never exposed server-side |
| **Voice STT** | Web Speech API (browser-native, no third-party service) |
| **Voice TTS** | SpeechSynthesis API — Daniel voice, rate 0.92, pitch 0.88 |
| **Fonts** | Cormorant Garamond (editorial/italic) + Inter (body) via Google Fonts |

---

## Agent Avatar System

Each agent is rendered as a 3D glossy ball using CSS radial gradients:

| Agent | Gradient |
|---|---|
| Greeter (G) | `radial-gradient(circle at 35% 35%, #b0b0b0, #606060, #2a2a2a)` |
| Technical (T) | `radial-gradient(circle at 35% 35%, #6ecfa0, #2d6a4f, #0f3320)` |
| GTM (M) | `radial-gradient(circle at 35% 35%, #f0c060, #b45309, #6b2e00)` |
| Executive (E) | `radial-gradient(circle at 35% 35%, #b48df0, #6d28d9, #320a7a)` |

---

## Design System

| Token | Value |
|---|---|
| `--accent` | `#b85042` |
| `--ink` | `#1a1a2e` |
| `--bg` | `#f8f4ee` (matches vjra.foundation) |
| `--surface` | `#f4f3f0` |
| `--border` | `#e8e6e1` |
| `--green` | `#2d6a4f` |
| `--amber` | `#b45309` |
| `--purple` | `#6d28d9` |

---

## Key Technical Decisions

**Why static hosting (no backend)?**  
Eliminates server cost and deployment complexity. The API key lives in `sessionStorage` — scoped per tab, never persisted or server-exposed. The `anthropic-dangerous-direct-browser-access` header enables direct browser-to-API calls.

**Why multi-agent instead of one large prompt?**  
- Each subagent has a short, focused system prompt → higher response quality
- Information is scoped per domain → no leakage (e.g. marketing budget in a technical answer)
- Each agent is independently testable and debuggable

**Why KB files in JS constants (not RAG at runtime)?**  
For a demo/prototype, embedding KBs in the static file eliminates the need for a running vector DB server. The Pinecone architecture is documented for a production deployment where KB files would be chunked, embedded, and retrieved dynamically.

---

## File Structure

```
vjra-research/
└── launch.html          # Entire application — UI, agents, KB data, voice, CSS
```

All logic, styles, KB data, agent prompts, and UI are self-contained in `launch.html`.

---

## Live URL

**[vjra.us/launch.html](https://vjra.us/launch.html)**
