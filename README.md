# Product Launch Command Center
Multi-agent voice + text AI system powered by Claude (Anthropic).

Stakeholders ask questions about a product launch and get automatically routed to the right specialist — Technical Readiness, GTM & Marketing, or Executive Briefing.

## Architecture

```
User input (text or voice)
        │
        ▼
   Greeter Agent          ← routes based on intent
   /      |      \
  ▼       ▼       ▼
Tech    GTM    Executive   ← each has scoped KB
  \      |      /
   ▼     ▼     ▼
     End Call             ← graceful exit
```

Cross-routing: any specialist can re-route to another if the question is off-topic.

## Agents

| Agent | Covers | Knowledge Base |
|---|---|---|
| Greeter | Intent detection, routing | None |
| Technical Readiness | Sprint status, QA, deployment, bugs, infra | Launch Plan + Technical KB |
| GTM & Marketing | Campaigns, press, sales, competitive | Launch Plan + GTM KB |
| Executive Briefing | Status, risks, budget, milestones | All 3 KB files |

## Setup

```bash
# 1. Clone / navigate to repo
cd product-launch-command-center

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here
# or copy .env.example → .env and fill it in

# 4. Run
python main.py              # text mode
python main.py --voice      # voice mode (mic + macOS TTS)
python main.py --voice --no-tts  # voice input, text output
```

## Voice Requirements

- **STT**: Google Speech Recognition via `SpeechRecognition` library (free, requires internet)
- **TTS**: macOS `say` command (built-in, no setup needed)
- Microphone access required for voice mode

## Sample Questions to Try

**Technical:**
- "What's the current sprint status?"
- "How many P1 bugs are open?"
- "What are the rollback criteria?"
- "Who's on-call during launch week?"

**GTM & Marketing:**
- "What's the press embargo date?"
- "How much are we spending on paid social?"
- "What's our messaging against ShopFast?"

**Executive:**
- "Give me a quick status update on the launch."
- "What are our biggest risks right now?"
- "Are we on track for April 15?"
