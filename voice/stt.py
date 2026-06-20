import sys


def listen(timeout: int = 10, phrase_limit: int = 15) -> str | None:
    """
    Record from microphone and transcribe using Google Speech Recognition (free tier).
    Returns transcribed text or None on failure.
    Requires: pip install SpeechRecognition pyaudio
    """
    try:
        import speech_recognition as sr
    except ImportError:
        print("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")
        sys.exit(1)

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("🎤 Listening... (speak now)")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None

    print("⏳ Transcribing...")
    try:
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None
