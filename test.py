import pytts
import platform

aws_access_key_id = "YOUR ACCESS KEY ID HERE"
aws_secret_access_key = "YOUR SECRET ACCESS KEY HERE"

# gTTS test
pytts.gtts().speak("Hello, World!")

# Amazon Polly test
pytts.polly(aws_access_key_id, aws_secret_access_key, "ap-southeast-2", "Olivia", "neural").speak("Hello, World!")

# Google Cloud Text-To-Speech test
pytts.gctts().speak("Hello, World!")

# pyttsx3 test
pytts.pyttsx3().speak("Hello, World!")

# Pico test
if platform.system() == "Linux":
    pytts.pico().speak("Hello, World!")

# SAPI test
if platform.system() == "Windows":
    pytts.sapi().speak("Hello, World!")

# NSSpeechSynthesizer test
if platform.system() == "Darwin":
    pytts.nsss().speak("Hello, World!")