import re
import anthropic
from .prompts import GREETER_PROMPT, TECHNICAL_PROMPT, GTM_PROMPT, EXECUTIVE_PROMPT
from .knowledge_base import KB_TECHNICAL, KB_GTM, KB_EXECUTIVE

MODEL = "claude-sonnet-4-6"

# Map agent name → (system prompt, knowledge base or None)
AGENTS = {
    "greeter":    (GREETER_PROMPT,   None),
    "technical":  (TECHNICAL_PROMPT, KB_TECHNICAL),
    "gtm":        (GTM_PROMPT,       KB_GTM),
    "executive":  (EXECUTIVE_PROMPT, KB_EXECUTIVE),
}

ROUTE_RE = re.compile(r"ROUTE:\s*(technical|gtm|executive|end)", re.IGNORECASE)


def _build_system(prompt: str, kb: str | None) -> str:
    if kb:
        return f"{prompt}\n\n---\n## KNOWLEDGE BASE\n\n{kb}"
    return prompt


def _extract_route(text: str) -> str | None:
    m = ROUTE_RE.search(text)
    return m.group(1).lower() if m else None


def _strip_route(text: str) -> str:
    return ROUTE_RE.sub("", text).strip()


class CommandCenter:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.current_agent = "greeter"
        self.history: list[dict] = []
        self.started = False

    def _call_agent(self, agent_name: str, user_message: str) -> tuple[str, str | None]:
        """Call an agent. Returns (cleaned_response, route_or_None)."""
        prompt, kb = AGENTS[agent_name]
        system = _build_system(prompt, kb)

        messages = self.history + [{"role": "user", "content": user_message}]

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        raw = response.content[0].text
        route = _extract_route(raw)
        clean = _strip_route(raw)
        return clean, route

    def greet(self) -> str:
        """Return the opening greeting without consuming a user turn."""
        self.started = True
        return (
            "Hi! Welcome to the Project Nightingale Launch Command Center. "
            "I can help with technical readiness and engineering status, "
            "marketing and go-to-market updates, or a high-level executive briefing. "
            "What are you looking for today?"
        )

    def chat(self, user_message: str) -> tuple[str, bool]:
        """
        Process a user message. Returns (response_text, is_done).
        Handles routing transparently — the caller sees only the final response.
        """
        max_hops = 3
        hops = 0

        while hops < max_hops:
            response, route = self._call_agent(self.current_agent, user_message)
            hops += 1

            if route == "end":
                farewell = "Thanks for checking in on Project Nightingale. Good luck with the launch!"
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": farewell})
                return farewell, True

            if route and route != self.current_agent:
                # Cross-route: switch agent and re-run (don't expose the route to user)
                self.current_agent = route
                continue

            # Valid response — commit to history and return
            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": response})
            return response, False

        # Fallback if routing loops
        fallback = "I'm having trouble routing your question. Could you rephrase it?"
        return fallback, False

    def reset(self):
        self.current_agent = "greeter"
        self.history = []
        self.started = False
