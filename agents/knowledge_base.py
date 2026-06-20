import os

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")

def _load(filename: str) -> str:
    path = os.path.join(KB_DIR, filename)
    with open(path, "r") as f:
        return f.read()

LAUNCH_PLAN = _load("KB_Launch_Plan.txt")
TECHNICAL = _load("KB_Technical_Readiness.txt")
GTM = _load("KB_GTM_Marketing.txt")

# Scoped KB bundles per agent
KB_TECHNICAL = f"{LAUNCH_PLAN}\n\n{TECHNICAL}"
KB_GTM = f"{LAUNCH_PLAN}\n\n{GTM}"
KB_EXECUTIVE = f"{LAUNCH_PLAN}\n\n{TECHNICAL}\n\n{GTM}"
