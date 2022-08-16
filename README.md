# pytts
pytts is a simple wrapper around many TTS synthesisers that caches spoken text. The main highlight is that the output is saved in audio files and played back rather than being generated again each time. This is useful for slow devices such as the Raspberry Pi Zero and can save bandwidth, speed up text generation and works offline for cloud based services.

## TTS synthesisers supported
- Google Text-to-Speech
- Pico
- Amazon Polly
- Windows SAPI
- NSSpeechSynthesizer
- Google Cloud Text-To-Speech
- pyttsx3 (SAPI, NSSpeechSynthesizer, espeak)

## Notes
- Amazon Polly and Google Cloud Text-To-Speech are paid services
- SAPI only works on Windows
- NSSpeechSynthesizer only works on MacOS
- Google Text-to-Speech, Amazon Polly and Google Cloud Text-To-Speech require an internet connection to generate new speech

## To do
- [ ] logging
- [x] database of previously spoken text rather than using as file name
- [x] documentation (a work in progress)
- [x] don't cache sensitive content
- [ ] blocking and non-blocking synthesis/playback
- [ ] asyncio support
- [ ] implement espeak, remove pyttsx3
- [ ] language/voice selection
- [ ] speed selection
- [ ] automatic synthesiser selection (based on OS and internet connection, paid services excluded by default)
- [ ] festival support
- [x] command line interface
- [x] REST API for usage from remote devices (such as ESP32)
- [x] socket API for usage from remote devices (such as ESP32)
- [x] implement tkinter GUI
- [ ] implement PyQt6 GUI
- [ ] implement Web GUI
- [ ] Android app

## Installation
To just download:
```
git clone https://github.com/BenjaminMickler/pytts.git
```
Or to install with pip:
```
python3 -m pip install git+https://github.com/BenjaminMickler/pytts.git
```
To install all requirements:
```
python3 -m pip install -r requirements.txt
```
It may be smarter to only install the TTS synthesisers that you are planing to use.
### Pico setup
To use Pico, you will need to compile it first.
First, clone the `py-ttspico` repository:
```
git clone https://github.com/sevangelatos/py-ttspico.git
```
and navigate into it:
```
cd py-ttspico
```
To just compile:
```
python3 setup.py build
```
Or to compile and install:
```
python3 setup.py install
```

## Usage
### Command line
```
usage: pytts [options] text

Synthesize text using a range of TTS engines

positional arguments:
  text                  the text to be spoken

options:
  -h, --help            show this help message and exit
  -v, --verbose         print a lot of information, useful for debugging
  -e ENGINE, --engine ENGINE
                        the TTS engine/synthesizer to use
  -ss, --socket-server  run a socket server
  -sc, --socket-client  run a socket client
  -rs, --rest-server    run a REST API server
  -rc, --rest-client    run a REST API client
  -p PORT, --port PORT  the port to use for the client/server
  -i IP, --ip IP        the IP address to use for the client/server

https://benmickler.com/
```
### Module
pytts has a class for each synthesiser. The classes are:
- polly
- gtts
- pico
- sapi
- nsss
- pyttsx3
- gctts

Each class currently only has one method: `speak(text, sensitive=False)`
If `sensitive` is true, the audio file will not be cached in the regular directory but rather a `tempfile.TemporaryDirectory()`, where it will only be accessible from this running program and will be destroyed with the program.

Some classes such as polly have different parameters. Until I have written documentation, you'll have to look at the source code.
```Python
import pytts
x = pytts.gtts()
x.speak("Hello, World!")
```
The path of the temporary directory (only used for Pico) is defined by the global variable `TMP_DIR`. The default temporary directory is `.tmp`.
The path of the TTS directory (used to store all previously spoken text) is defined by the global variable `TTS_DIR`. The default TTS directory is `.tts`.
The database is stored in `TTS_DIR/tts.db`.

## Documentation
The documentation for pytts can be found at https://pytts.docs.benmickler.com