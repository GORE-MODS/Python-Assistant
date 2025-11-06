import pvporcupine
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import struct
import pyaudio
import os
import threading
import tkinter as tk
from tkinter import scrolledtext

# --- CONFIG ---
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
model = genai.GenerativeModel("gemini-1.5-flash")

WAKE_WORD_MODEL = "HeyGrav.ppn"  # Path to your wake-word file

# --- Setup ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)

# --- GUI ---
root = tk.Tk()
root.title("Grav Voice Assistant")
root.geometry("500x400")
root.resizable(False, False)

status_label = tk.Label(root, text="Status: Idle", font=("Helvetica", 14), fg="white", bg="gray")
status_label.pack(fill=tk.X)

chat_box = scrolledtext.ScrolledText(root, state='disabled', wrap='word')
chat_box.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

def log_message(sender, message):
    chat_box.config(state='normal')
    chat_box.insert(tk.END, f"{sender}: {message}\n")
    chat_box.see(tk.END)
    chat_box.config(state='disabled')

def speak(text):
    log_message("Grav", text)
    engine.say(text)
    engine.runAndWait()

def listen_command(timeout=6, phrase_time_limit=7):
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        status_label.config(text="Status: Listening...", bg="green")
        root.update()
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio).lower()
            log_message("You", text)
            return text
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            return ""
        except sr.RequestError:
            speak("Speech service is unavailable.")
            return ""
        finally:
            status_label.config(text="Status: Idle", bg="gray")
            root.update()

def get_ai_response(prompt):
    response = model.generate_content(prompt)
    return response.text

# --- Main assistant loop ---
def assistant_loop():
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
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                # Wake word detected
                status_label.config(text="Status: Wake-word detected!", bg="orange")
                root.update()
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

# --- Run assistant in separate thread so GUI stays responsive ---
threading.Thread(target=assistant_loop, daemon=True).start()
root.mainloop()
