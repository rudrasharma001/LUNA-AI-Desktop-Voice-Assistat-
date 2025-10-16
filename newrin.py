# -*- coding: utf-8 -*-

import speech_recognition as sr
import webbrowser
import pywhatkit
import asyncio
import subprocess
import datetime
import os
import pyautogui
import time
import threading
import pystray
import requests
from PIL import Image, ImageDraw
from edge_tts import Communicate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("Luna script started running...")


voice = "en-US-AriaNeural"

def speak(text):
    try:
        print(f"Luna: {text}")

        async def _speak_async(voice_name, content, save_file="tts_output.mp3"):
            communicate = Communicate(text=content, voice=voice_name)
            await communicate.save(save_file)

        try:
            asyncio.run(asyncio.wait_for(_speak_async(voice, text), timeout=20))
        except Exception as e:
            print(f"TTS failed: {e}. Falling back to print only.")
            return

        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "tts_output.mp3"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )
        except Exception as e:
            print("Audio playback error:", e)

    except Exception as e:
        print("Speech error:", e)

def hear_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=1)
        r.energy_threshold = max(150, getattr(r, "energy_threshold", 300))
        r.pause_threshold = 0.6
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return ""
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception as e:
        print("Unexpected recognition error:", e)
        return ""
    return query.lower()

PERPLEXITY_API_KEY = "Paste Your Perplexity API Key Here"

def ask_perplexity(question):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are LUNA, a helpful AI assistant."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 600,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
        result = response.json()
        try:
            return result["choices"][0]["message"]["content"]
        except Exception:
            return str(result)
    except Exception as e:
        return f"Request failed: {e}"

def generate_code(description, language="python"):
    extensions = {
        "python": ".py",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "html": ".html",
        "javascript": ".js",
    }
    ext = extensions.get(language.lower(), ".txt")
    filename = f"GeneratedCode{ext}"

    prompt = f"Write {language} code for: {description}. Only give the code."
    code = ask_perplexity(prompt)

    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:-1])

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        subprocess.Popen(["notepad.exe", filename])
        speak(f"Here is the {language} code. I have opened it in Notepad.")
    except Exception as e:
        speak(f"Sorry, I could not save the code. {e}")


def notepad_khol_muh_se_bol():
    speak("Opening Notepad and starting dictation mode.")
    try:
        subprocess.Popen(["notepad.exe"])
    except FileNotFoundError:
        speak("Notepad was not found on this system.")
        return
    time.sleep(1)
    try:
        pyautogui.typewrite("Dictation mode activated. Start speaking...\n")
    except Exception:
        pass

    recognizer = sr.Recognizer()
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
                        try:
                            pyautogui.typewrite(text + " ")
                        except Exception:
                            print(f"[Dictation] {text}")
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    speak("Sorry, I didn't catch that.")
                    continue
                except sr.RequestError:
                    speak("Speech service is unavailable right now.")
                    continue
        except Exception as e:
            print("Microphone loop error:", e)
            break


def process_command(cmd):
    if not cmd:
        return
    cmd = cmd.lower()

    if "generate code" in cmd:
        try:
            if " in " in cmd:
                parts = cmd.split(" in ")
                description = parts[0].replace("generate code for", "").replace("generate code", "").strip()
                language = parts[1].strip()
            else:
                description = cmd.replace("generate code for", "").replace("generate code", "").strip()
                language = "python"
            generate_code(description, language)
        except Exception as e:
            speak("I couldn't generate the code right now.")
            print("Code generation error:", e)

    elif cmd.startswith("play "):
        song = cmd.replace("play", "", 1).strip()
        if song:
            speak(f"Playing {song} on YouTube")
            pywhatkit.playonyt(song)
        else:
            speak("Please tell me which song to play.")

    elif cmd.startswith("search "):
        query = cmd.replace("search", "", 1).strip()
        speak(f"Searching Google for {query}")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    elif any(cmd.startswith(prefix) for prefix in ("who", "what", "how", "why", "when", "where", "which")) \
         or any(phrase in cmd for phrase in ("tell me", "explain", "define", "?")):
        answer = ask_perplexity(cmd)
        print(f"\nAnswer from Perplexity:\n{answer}\n")
        speak(answer)

    elif "open youtube" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open google" in cmd:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif "shutdown" in cmd or "shut down" in cmd:
        speak("Shutting down your system.")
        try:
            subprocess.run("shutdown /s /t 1", shell=True)
        except Exception as e:
            speak("Unable to shutdown: " + str(e))

    elif "exit" in cmd or "stop" in cmd or "quit" in cmd:
        speak("Goodbye.")
        raise SystemExit

    elif cmd.startswith("message "):
        try:
            cmd = cmd.replace("message", "", 1).strip()
            if "saying" in cmd:
                contact_name, message = cmd.split("saying", 1)
            else:
                contact_name, message = cmd, "Hello!"

            contact_name = contact_name.strip()
            message = message.strip()

            speak(f"Messaging {contact_name} on WhatsApp.")

           
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite("whatsapp")
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(3)

           
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.5)
            pyautogui.typewrite(contact_name)
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(1)

           
            pyautogui.typewrite(message)
            time.sleep(0.5)
            pyautogui.press("enter")

            speak(f"Message sent to {contact_name}.")

        except Exception as e:
            speak("Sorry, I couldn't send the message.")
            print("Error:", e)

    elif "open notepad" in cmd or "start dictation" in cmd:
        notepad_khol_muh_se_bol()

    elif cmd.startswith("open "):
        app_name = cmd.replace("open", "").strip()
        if app_name:
            speak(f"Opening {app_name}")
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite(app_name)
            time.sleep(0.5)
            pyautogui.press("enter")
        else:
            speak("Please tell me the app name to open.")

    elif "set an alarm" in cmd:
        try:
            parts = cmd.split("for")
            if len(parts) > 1:
                time_part = parts[1].strip()
                if "second" in time_part:
                    seconds = int(time_part.split()[0])
                elif "minute" in time_part:
                    seconds = int(time_part.split()[0]) * 60
                elif "hour" in time_part:
                    seconds = int(time_part.split()[0]) * 3600
                else:
                    speak("I couldn't understand the time duration.")
                    return
                set_alarm(seconds)
            else:
                speak("Please tell me how long to set the alarm for.")
        except Exception as e:
            speak(f"Sorry, I couldn't set the alarm. {e}")

    elif "shutdown in" in cmd:
        try:
            parts = cmd.split("in")
            if len(parts) > 1:
                time_part = parts[1].strip()
                if "second" in time_part:
                    seconds = int(time_part.split()[0])
                elif "minute" in time_part:
                    seconds = int(time_part.split()[0]) * 60
                elif "hour" in time_part:
                    seconds = int(time_part.split()[0]) * 3600
                else:
                    speak("I couldn't understand the time duration.")
                    return
                set_timed_shutdown(seconds)
            else:
                speak("Please tell me the shutdown timer duration.")
        except Exception as e:
            speak(f"Sorry, I couldn't set the timed shutdown. {e}")

    else:
        speak("Sorry, I didn't understand that.")


def set_alarm(seconds):
    def alarm_thread():
        time.sleep(seconds)
        speak("Alarm ringing now!")
        try:
            for _ in range(5):
                subprocess.run(["powershell", "-c", "[console]::beep(1000,500)"], shell=True)
        except Exception:
            pass
    threading.Thread(target=alarm_thread, daemon=True).start()
    speak(f"Alarm set for {seconds} seconds from now.")

def set_timed_shutdown(seconds):
    try:
        minutes = max(1, seconds // 60)
        subprocess.run(f"shutdown /s /t {seconds}", shell=True)
        speak(f"Your PC will shut down in {minutes} minute{'s' if minutes > 1 else ''}.")
    except Exception as e:
        speak(f"Failed to set timed shutdown. {e}")


def startup_restore():
    pass


def listen_command():
    return hear_voice()

def greet():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning. I am Luna. How can I help you today?")
    elif hour < 18:
        speak("Good afternoon. I am Luna. How can I help you today?")
    else:
        speak("Good evening. I am Luna. How can I help you today?")


def main():
    try:
        startup_restore()
    except Exception as e:
        print("startup_restore error:", e)

    try:
        greet()
    except Exception as e:
        print("greet error:", e)

    while True:
        command = listen_command()
        if not command:
            continue

        if "hello luna" in command or command.strip() == "luna":
            speak("Yes? I'm listening.")
            followup = listen_command()
            if followup:
                process_command(followup)
            else:
                speak("I didn't hear a command.")
        else:
            process_command(command)

if __name__ == "__main__":
    main()

