#!/usr/bin/env python3
"""
Product Launch Command Center
Multi-agent voice + text AI system powered by Claude.

Usage:
  python main.py              # text mode (default)
  python main.py --voice      # voice mode (mic input + TTS output)
  python main.py --voice --no-tts  # voice input, text output
"""

import argparse
import sys
from agents.orchestrator import CommandCenter
from voice.tts import speak
from voice.stt import listen


def run_text(center: CommandCenter):
    greeting = center.greet()
    print(f"\n🤖 Command Center: {greeting}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "q"}:
            print("🤖 Command Center: Goodbye!")
            break

        response, done = center.chat(user_input)
        print(f"\n🤖 Command Center [{center.current_agent.upper()}]: {response}\n")

        if done:
            break


def run_voice(center: CommandCenter, use_tts: bool = True):
    greeting = center.greet()
    print(f"\n🤖 Command Center: {greeting}\n")
    if use_tts:
        speak(greeting)

    while True:
        user_input = listen()

        if user_input is None:
            hint = "I didn't catch that. Try again or press Ctrl+C to exit."
            print(f"🤖 Command Center: {hint}")
            if use_tts:
                speak(hint)
            continue

        if user_input.lower() in {"exit", "quit", "goodbye", "bye", "stop"}:
            farewell = "Goodbye!"
            print(f"🤖 Command Center: {farewell}")
            if use_tts:
                speak(farewell)
            break

        response, done = center.chat(user_input)
        agent_label = center.current_agent.upper()
        print(f"\n🤖 Command Center [{agent_label}]: {response}\n")
        if use_tts:
            speak(response)

        if done:
            break


def main():
    parser = argparse.ArgumentParser(description="Product Launch Command Center")
    parser.add_argument("--voice", action="store_true", help="Enable voice input mode")
    parser.add_argument("--no-tts", action="store_true", help="Disable TTS output (voice input only)")
    args = parser.parse_args()

    center = CommandCenter()

    print("=" * 60)
    print("  PROJECT NIGHTINGALE — Launch Command Center")
    print("  Powered by Claude (Multi-Agent)")
    print("=" * 60)

    if args.voice:
        print("Mode: VOICE (mic input" + (" + TTS" if not args.no_tts else ", text output") + ")")
        print("Press Ctrl+C to exit at any time.\n")
        run_voice(center, use_tts=not args.no_tts)
    else:
        print("Mode: TEXT (type your questions)")
        print("Type 'exit' or press Ctrl+C to quit.\n")
        run_text(center)


if __name__ == "__main__":
    main()
