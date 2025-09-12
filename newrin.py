import speech_recognition as sr
import webbrowser
import wikipedia
import pywhatkit
import asyncio
import subprocess
import datetime
import os
import pyautogui
import time
import requests

# Speak using Edge TTS
from edge_tts import Communicate

def speak(text):
    print(f"Luna: {text}")  # 👈 Print what Luna says
    async def _speak_async():
        communicate = Communicate(text=text, voice="en-IN-NeerjaNeural")
        await communicate.save("tts_output.mp3")

    try:
        asyncio.run(_speak_async())
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "tts_output.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("Speech error:", e)


# Recognize voice
def listen_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=1)  # auto-calibration
        r.energy_threshold = 200   # more sensitive
        r.pause_threshold = 0.6    # quicker response
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "Sorry, I couldn't reach Google servers."

    return query.lower()

PERPLEXITY_API_KEY = "Paste Your Perplexity API Key here"

# ✅ Fixed Perplexity function
def ask_perplexity(question):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "pplx-7b-online",   # or pplx-70b-chat
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # Extract answer safely
        reply = (
            result["choices"][0].get("message", {}).get("content")
            or result["choices"][0].get("text", "")
        )
        return reply.strip()
    except Exception as e:
        return f"Error reaching Perplexity: {e}\nDetails: {response.text if 'response' in locals() else ''}"

# Process voice commands
def process_command(cmd):
    cmd = cmd.lower()

    if "play" in cmd:
        song = cmd.replace("play", "").strip()
        speak(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)

    elif "search" in cmd:
        query = cmd.replace("search", "").strip()
        speak(f"Searching Google for {query}")
        webbrowser.open(f"https://www.google.com/search?q={query}")
    elif cmd.startswith(("who", "what", "how", "why", "when", "in", "where", "which", "tell me", "explain", "define")):
        answer = ask_perplexity(cmd)
        print(f"Answer from Perplexity:\n{answer}\n")
        speak(answer)



    elif "open youtube" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open google" in cmd:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif "shutdown" in cmd or "shut down" in cmd:
        speak("Shutting down your system sir.")
        subprocess.run("shutdown /s /t 1", shell=True)

    elif "exit" in cmd or "stop" in cmd:
        speak("Goodbye sir.")
        exit()

    elif "open notepad" in cmd:
        open_notepad_and_dictate()

    else:
        speak("Sorry, I didn't understand that.")

# Greet on start
def greet():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning sir. I am Luna. How can I help you today?")
    elif hour < 18:
        speak("Good afternoon sir. I am Luna. How can I help you today?")
    else:
        speak("Good evening sir. I am Luna. How can I help you today?")

def open_notepad_and_dictate():
    speak("Opening Notepad and starting dictation mode.")
    subprocess.Popen(["notepad.exe"])
    time.sleep(1)  # give Notepad a second to open
    pyautogui.typewrite("Dictation mode activated. Start speaking...\n")

    recognizer = sr.Recognizer()  # ✅ define here

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)

                try:
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio).lower()

                    if "stop writing" in text:
                        speak("Stopping dictation mode.")
                        break
                    else:
                        pyautogui.typewrite(text + " ")

                except sr.WaitTimeoutError:
                    speak("I didn’t hear anything, please say again.")
                    continue

        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
        except sr.RequestError:
            speak("Speech service is unavailable right now.")

def ask_perplexity(question):
    PERPLEXITY_API_KEY = "Paste Your Perplexity API Key here"

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "sonar",  # One of the valid model names
        "messages": [
            {"role": "system", "content": "You are LUNA, a helpful AI assistant."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Request failed: {e}"




# Main loop
def main():
    greet()
    while True:
        command = listen_command()

        if "hello luna" in command:   # respond naturally to 'luna'
            speak("Yes sir?")
            command = listen_command()
            process_command(command)

if __name__ == "__main__":
    main()
