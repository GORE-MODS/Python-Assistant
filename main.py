import pvporcupine
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import struct
import pyaudio
import os

# --- CONFIG ---
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
model = genai.GenerativeModel("gemini-1.5-flash")

recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)

WAKE_WORD_MODEL = "HeyGrav.ppn"  # Path to your wake-word file

def speak(text):
    print("Grav:", text)
    engine.say(text)
    engine.runAndWait()

def listen_command(timeout=6, phrase_time_limit=7):
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎙️ Listening for command…")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio).lower()
            print("You:", text)
            return text
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            return ""
        except sr.RequestError:
            speak("Speech service is unavailable.")
            return ""

def get_ai_response(prompt):
    response = model.generate_content(prompt)
    return response.text

def main():
    speak("Hey, I'm Grav. Say 'Hey Grav' when you need me.")

    porcupine = pvporcupine.create(keywords=[], custom_keyword_paths=[WAKE_WORD_MODEL])

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    try:
        while True:
            pcm = stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            result = porcupine.process(pcm)
            if result >= 0:
                # Wake word detected
                speak("Yes?")
                command = listen_command()
                if not command:
                    speak("I didn't catch that.")
                    continue
                if any(x in command for x in ["exit", "quit", "stop"]):
                    speak("Goodbye.")
                    break
                elif "open" in command:
                    app = command.replace("open","").strip()
                    if app:
                        os.system(f"start {app}")
                        speak(f"Opening {app}")
                    else:
                        speak("What should I open?")
                else:
                    reply = get_ai_response(command)
                    speak(reply)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    main()
