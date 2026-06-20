import subprocess
import shutil


def speak(text: str, voice: str = "Samantha") -> None:
    """Speak text using macOS `say` command (built-in, no dependencies)."""
    if not shutil.which("say"):
        print(f"[TTS unavailable] {text}")
        return
    # Rate 180 wpm feels natural for a command center voice
    subprocess.run(["say", "-v", voice, "-r", "180", text], check=True)
