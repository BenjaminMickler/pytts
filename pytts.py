__author__ = "Benjamin Mickler"
__copyright__ = "Copyright 2022, Benjamin Mickler"
__credits__ = ["Benjamin Mickler"]
__license__ = "GPLv3 or later"
__version__ = "16082022"
__maintainer__ = "Benjamin Mickler"
__email__ = "ben@benmickler.com"

"""
pytts is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

pytts is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
pytts. If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
from codecs import StreamReader
import sys
import tkinter
from tkinter import filedialog
import wave
import os
import shutil
import tempfile
import sqlite3
import uuid
import asyncio
import io
import json
import tkinter as tk
import time

import requests
from playsound import playsound

try:
    from gtts import gTTS
except:
    pass
try:
    import boto3
except:
    pass
try:
    import ttspico
except:
    pass
try:
    import win32com.client
except:
    pass
try:
    from AppKit import NSSpeechSynthesizer
    import Foundation
except:
    pass
try:
    import pyttsx3 as _pyttsx3
except:
    pass
try:
    import google.cloud.texttospeech as _gctts
except:
    pass
try:
    from fastapi import FastAPI, APIRouter, Request
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except:
    pass

TMP_DIR = ".tmp"
TTS_DIR = ".tts"
if not os.path.isdir(TTS_DIR):
    os.mkdir(TTS_DIR)
if not os.path.isdir(TMP_DIR):
    os.mkdir(TMP_DIR)
SENSITIVE_DIR = tempfile.TemporaryDirectory()
connection = sqlite3.connect(TTS_DIR+"/tts.db")
cursor = connection.cursor()
cursor.execute("create table if not exists polly (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists gtts (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists pico (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists sapi (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists nsss (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists pyttsx3 (text TEXT, uuid TEXT)")
cursor.execute("create table if not exists gctts (text TEXT, uuid TEXT)")


def add_row(table, text, row_uuid):
    cursor.execute("INSERT INTO "+table +
                   " (text, uuid) VALUES (?, ?)", (text, row_uuid))
    connection.commit()
    return uuid


def row_exists_by_uuid(table, uuid):
    cursor.execute("SELECT * FROM "+table+" WHERE uuid = ?", (uuid,))
    return cursor.fetchone() is not None


def row_exists_by_text(table, text):
    cursor.execute("SELECT * FROM "+table+" WHERE text = ?", (text,))
    return cursor.fetchone() is not None


def get_text_by_uuid(table, uuid):
    cursor.execute("SELECT text FROM "+table+" WHERE uuid = ?", (uuid,))
    return cursor.fetchone()[0]


def get_uuid_by_text(table, text):
    cursor.execute("SELECT uuid FROM "+table+" WHERE text = ?", (text,))
    return cursor.fetchone()[0]


if not os.path.isdir(TMP_DIR):
    os.mkdir(TMP_DIR)
if not os.path.isdir(TTS_DIR):
    os.mkdir(TTS_DIR)


def cleanup():
    SENSITIVE_DIR.cleanup()
    shutil.rmtree(TMP_DIR)


class polly:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str, VoiceId: str, engine: str, output_format: str = "mp3"):
        """_summary_

        Args:
            aws_access_key_id (str): _description_
            aws_secret_access_key (str): _description_
            region_name (str): _description_
            VoiceId (str): _description_
            engine (str): _description_
            output_format (str, optional): _description_. Defaults to "mp3".
        """
        self.output_format = output_format
        self.VoiceId = VoiceId
        self.engine = engine
        if not os.path.isdir(TTS_DIR+"/polly"):
            os.mkdir(TTS_DIR+"/polly")
        self.polly_client = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name).client('polly')

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("polly", text):
            text_uuid = get_uuid_by_text("polly", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/polly/"+text_uuid+"."+self.output_format
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+"."+self.output_format
        if not row_exists_by_uuid("polly", text_uuid) or sensitive:
            response = self.polly_client.synthesize_speech(VoiceId=self.VoiceId,
                                                           OutputFormat=self.output_format,
                                                           Text=text,
                                                           Engine=self.engine)
            with open(fn, 'wb') as f:
                f.write(response['AudioStream'].read())
            add_row("polly", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class gtts:
    def __init__(self, lang: str = "en"):
        """_summary_

        Args:
            lang (str, optional): _description_. Defaults to "en".
        """
        self.lang = lang
        if not os.path.isdir(TTS_DIR+"/gtts"):
            os.mkdir(TTS_DIR+"/gtts")

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("gtts", text):
            text_uuid = get_uuid_by_text("gtts", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/gtts/"+text_uuid+".mp3"
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+".mp3"
        if not row_exists_by_uuid("gtts", text_uuid) or sensitive:
            gttsobj = gTTS(text=text, lang=self.lang, slow=False)
            gttsobj.save(fn)
            add_row("gtts", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class pico:
    def __init__(self, lang: str = "en-US"):
        """_summary_

        Args:
            lang (str, optional): _description_. Defaults to "en-US".
        """
        self.lang = lang
        self.engine = ttspico.TtsEngine(self.lang, lang_dir="lang")
        if not os.path.isdir(TMP_DIR+"/pico"):
            os.mkdir(TMP_DIR+"/pico")
        if not os.path.isdir(TTS_DIR+"/pico"):
            os.mkdir(TTS_DIR+"/pico")

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("pico", text):
            text_uuid = get_uuid_by_text("pico", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/pico/"+text_uuid+".wav"
        raw_fn = TMP_DIR+"/pico/"+text_uuid+".raw"
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+".wav"
            raw_fn = SENSITIVE_DIR.name+"/"+text_uuid+".raw"
        if not row_exists_by_uuid("pico", text_uuid) or sensitive:
            audio = self.engine.speak(text)
            with open(raw_fn, "wb") as outfile:
                outfile.write(audio)
            with open(raw_fn, 'rb') as pcmfile:
                pcmdata = pcmfile.read()
            with wave.open(fn, 'wb') as wavfile:
                wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
                wavfile.writeframes(pcmdata)
            add_row("pico", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class sapi:
    def __init__(self):
        if not os.path.isdir(TTS_DIR+"/sapi"):
            os.mkdir(TTS_DIR+"/sapi")
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.filestream = win32com.client.Dispatch("SAPI.SpFileStream")

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("sapi", text):
            text_uuid = get_uuid_by_text("sapi", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/sapi/"+text_uuid+".wav"
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+".wav"
        if not row_exists_by_uuid("sapi", text_uuid) or sensitive:
            self.filestream.open(fn, 3, False)
            self.speaker.AudioOutputStream = self.filestream
            self.speaker.speak(text)
            self.filestream.close()
            add_row("sapi", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class nsss:
    def __init__(self):
        if not os.path.isdir(TTS_DIR+"/nsss"):
            os.mkdir(TTS_DIR+"/nsss")
        self.nssp = NSSpeechSynthesizer
        self.ve = self.nssp.alloc().init()
        self.ve.setRate_(100)

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("nsss", text):
            text_uuid = get_uuid_by_text("nsss", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/nsss/"+text_uuid+".aiff"
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+".aiff"
        if not row_exists_by_uuid("nsss", text_uuid) or sensitive:
            url = Foundation.NSURL.fileURLWithPath_(fn)
            self.ve.startSpeakingString_toURL_(text, url)
            add_row("nsss", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class pyttsx3:
    def __init__(self, lang: str = "en"):
        """_summary_

        Args:
            lang (str, optional): _description_. Defaults to "en".
        """
        self.lang = lang
        self.engine = _pyttsx3.init()
        if not os.path.isdir(TTS_DIR+"/pyttsx3"):
            os.mkdir(TTS_DIR+"/pyttsx3")

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("pyttsx3", text):
            text_uuid = get_uuid_by_text("pyttsx3", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/pyttsx3/"+text_uuid+".mp3"
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+".mp3"
        if not row_exists_by_uuid("pyttsx3", text_uuid) or sensitive:
            self.engine.save_to_file(text, fn)
            self.engine.runAndWait()
            add_row("pyttsx3", text, text_uuid)
            while not os.path.isfile(fn):
                time.sleep(0.1)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class gctts:
    def __init__(self, voice_name: str):
        """_summary_

        Args:
            voice_name (str): _description_
        """
        language_code = "-".join(voice_name.split("-")[:2])
        self.voice_params = _gctts.VoiceSelectionParams(
            language_code=language_code, name=voice_name
        )
        self.audio_config = _gctts.AudioConfig(
            audio_encoding=_gctts.AudioEncoding.LINEAR16)
        self.client = _gctts.TextToSpeechClient()
        if not os.path.isdir(TTS_DIR+"/gctts"):
            os.mkdir(TTS_DIR+"/gctts")

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """
        if row_exists_by_text("gctts", text):
            text_uuid = get_uuid_by_text("gctts", text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/gctts/"+text_uuid+".wav"
        if sensitive:
            fn = SENSITIVE_DIR+"/"+text_uuid+".wav"
        if not row_exists_by_uuid("nsss", text_uuid) or sensitive:
            text_input = _gctts.SynthesisInput(text=text)
            response = self.client.synthesize_speech(
                input=text_input, voice=self.voice_params, audio_config=self.audio_config
            )
            with open(fn, "wb") as out:
                out.write(response.audio_content)
            add_row("gctts", text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class custom:
    def __init__(self, name: str, tts_gen_func, file_ext: str=".mp3"):
        """Custom: a class that wraps a custom TTS
        generator function and caches the generated files.

        Args:
            name (str): _description_
            tts_gen_func (_type_): _description_
            file_ext (str, optional): _description_. Defaults to ".mp3".
        """        
        self.tts_gen_func = tts_gen_func
        self.name = name
        self.file_ext = file_ext
        if not os.path.isdir(TTS_DIR+"/"+name):
            os.mkdir(TTS_DIR+"/"+name)

    def speak(self, text: str, sensitive: bool = False, play: bool = True) -> str:
        """_summary_

        Args:
            text (str): _description_
            sensitive (bool, optional): _description_. Defaults to False.
            play (bool, optional): _description_. Defaults to True.

        Returns:
            str: _description_
        """        
        if row_exists_by_text(self.name, text):
            text_uuid = get_uuid_by_text(self.name, text)
        else:
            text_uuid = str(uuid.uuid4())
        fn = TTS_DIR+"/"+self.name+"/"+text_uuid+self.file_ext
        if sensitive:
            fn = SENSITIVE_DIR.name+"/"+text_uuid+self.file_ext
        if not row_exists_by_uuid(self.name, text_uuid) or sensitive:
            self.tts_gen_func(text, fn)
            add_row(self.name, text, text_uuid)
            if play:
                playsound(fn)
        else:
            if play:
                playsound(fn)
        return fn


class socket_api:
    def __init__(self, tts: pyttsx3 | gctts | nsss | sapi | pico | gtts | polly):
        """_summary_

        Args:
            tts (pyttsx3 | gctts | nsss | sapi | pico | gtts | polly): _description_
        """
        self.tts = tts

    async def handle(self, reader: StreamReader, writer):
        buffer = b""
        while True:
            while b"\r\n" not in buffer:
                data = await reader.read(100)
                if not data:
                    break
                buffer += data
            line, sep, buffer = buffer.partition(b"\r\n")
            data = line.decode()
            if data == "exit":
                writer.close()
                break
            try:
                data = json.loads(data)
            except:
                writer.write(
                    (json.dumps({"status": 1, "error": "invalid JSON"})+"\r\n").encode())
                await writer.drain()
            if "text" in data:
                # speak data["text"] using tts and send the audio file to the client
                fn = self.tts.speak(data["text"], data.get(
                    "sensitive", False), play=False)
                while not os.path.isfile(fn):
                    print("waiting for file to be created")
                with open(fn, "rb") as f:
                    writer.write(f.read())
                writer.write(b"\r\n")
                await writer.drain()
            else:
                writer.write(
                    (json.dumps({"status": 1, "error": "no text"})+"\r\n").encode())
                await writer.drain()

    async def run(self, port: int) -> None:
        """_summary_

        Args:
            port (int): _description_
        """
        server = await asyncio.start_server(self.handle, '0.0.0.0', port)
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        async with server:
            await server.serve_forever()


class socket_client:
    def __init__(self, ipaddr: str, port: int):
        self.ipaddr = ipaddr
        self.port = port

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ipaddr, self.port)
        return self.reader, self.writer

    async def speak(self, text: str, play: bool = True, save: bool = False) -> None:
        """_summary_

        Args:
            text (str): _description_
            play (bool, optional): _description_. Defaults to True.
            save (bool, optional): _description_. Defaults to False.
        """
        self.writer.write((json.dumps({"text": text})+"\r\n").encode())
        await self.writer.drain()
        buffer = b""
        while True:
            while b"\r\n" not in buffer:
                data = await self.reader.read(100)
                if not data:
                    break
                buffer += data
            line, sep, buffer = buffer.partition(b"\r\n")
            #bio = io.BytesIO(line)
            if play:
                if save != False:
                    with open(save, "wb") as f:
                        f.write(line)
                    playsound(save)
                else:
                    tmpfile = tempfile.NamedTemporaryFile()
                    with open(tmpfile.name, "wb") as f:
                        f.write(line)
                    playsound(tmpfile.name)


class _rest_api:
    def __init__(self, tts: pyttsx3 | gctts | nsss | sapi | pico | gtts | polly):
        """_summary_

        Args:
            tts (pyttsx3 | gctts | nsss | sapi | pico | gtts | polly): _description_
        """
        self.tts = tts
        self.router = APIRouter()
        self.router.add_api_route("/speak", self.speak, methods=["POST"])

    async def speak(self, info: Request) -> FileResponse:
        """_summary_

        Args:
            info (Request): _description_

        Returns:
            FileResponse: _description_
        """
        req_info = await info.json()
        fn = self.tts.speak(
            req_info["text"], sensitive=req_info["sensitive"], play=False)
        while not os.path.isfile(fn):
            print("waiting for file to be created")
        return FileResponse(fn)


async def create_server(app: FastAPI, port: int) -> None:
    """_summary_

    Args:
        app (FastAPI): _description_
        port (int): _description_
    """
    server_config = uvicorn.Config(app, port=port)
    server = uvicorn.Server(server_config)
    await server.serve()


def rest_api(tts: pyttsx3 | gctts | nsss | sapi | pico | gtts | polly) -> FastAPI:
    """_summary_

    Args:
        tts (pyttsx3 | gctts | nsss | sapi | pico | gtts | polly): _description_

    Returns:
        FastAPI: _description_
    """
    app = FastAPI()
    api_obj = _rest_api(tts)
    app.include_router(api_obj.router)
    return app


class rest_client:
    def __init__(self, ipaddr: str, port: int):
        """_summary_

        Args:
            ipaddr (str): _description_
            port (int): _description_
        """
        self.ipaddr = ipaddr
        self.port = port

    def speak(self, text: str, play: bool = True, save: bool = False) -> None:
        """_summary_

        Args:
            text (str): _description_
            play (bool, optional): _description_. Defaults to True.
            save (bool, optional): _description_. Defaults to False.
        """
        json_data = {
            "text": "hello world",
            "sensitive": False
        }
        response = requests.post(
            f"http://{self.ipaddr}:{self.port}/speak", json=json_data)
        if save != False:
            with open(save, "wb") as f:
                f.write(response.content)
        if play:
            if save != False:
                playsound(save)
            else:
                tmpfile = tempfile.NamedTemporaryFile()
                with open(tmpfile.name, "wb") as f:
                    f.write(response.content)
                playsound(tmpfile.name)


async def _socket_client(text, ipaddr: str, port: int) -> None:
    """_summary_

    Args:
        text (_type_): _description_
        ipaddr (str): _description_
        port (int): _description_
    """
    sc = socket_client(ipaddr, port)
    await sc.connect()
    await sc.speak(text)


class tkinter_GUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text to Speech")
        self.root.geometry("400x200")
        #scroll = tk.Scrollbar(self.root)
        #scroll.pack(side=tk.RIGHT, fill=tk.Y)
        # , yscrollcommand=scroll.set)
        self.text_entry = tk.Text(self.root, width=1, height=1)
        self.text_entry.pack(expand=True, fill=tk.BOTH, pady=(10, 0), padx=10)
        self.text_entry.focus_set()
        # scroll.config(command=self.text_entry.yview)
        #self.text_entry.bind("<Return>", self.speak)
        self.speak_button = tk.Button(
            self.root, text="Speak", command=self.speak)
        self.speak_button.pack()
        self.save_button = tk.Button(self.root, text="Save", command=self.save)
        self.save_button.pack()
        self.sensitive_var = tk.BooleanVar()
        self.sensitive_checkbutton = tk.Checkbutton(
            self.root, text="Sensitive", variable=self.sensitive_var)
        self.sensitive_checkbutton.pack()
        self.sensitive_var.set(False)
        self.synthesizers = tk.StringVar(self.root)
        self.synthesizers.set("pyttsx3")
        self.synthesizer_menu = tk.OptionMenu(self.root, self.synthesizers, "Amazon Polly", "pyttsx3",
                                              "Windows SAPI", "Pico", "Google Text-to-Speech", "Google Cloud Text-To-Speech", "NSSpeechSynthesizer")
        self.synthesizer_menu.pack()
        self.root.mainloop()

    def speak(self, *args, **kwargs) -> None:
        engines_prettynames[self.synthesizers.get()]().speak(
            self.text_entry.get("1.0", 'end-1c'), sensitive=self.sensitive_var.get())

    def save(self) -> None:
        fn = engines_prettynames[self.synthesizers.get()]().speak(self.text_entry.get(
            "1.0", 'end-1c'), sensitive=self.sensitive_var.get(), play=False)
        savefn = filedialog.asksaveasfilename()
        with open(fn, "rb") as f:
            with open(savefn, "wb") as sf:
                sf.write(f.read())


def web_GUI() -> FastAPI:
    """_summary_

    Returns:
        FastAPI: _description_
    """
    app = FastAPI()
    app.mount("/", StaticFiles(directory="static"), name="static")
    return app


async def rest_and_web_servers(args: argparse.Namespace) -> None:
    """_summary_

    Args:
        args (argparse.Namespace): _description_
    """
    done, pending = await asyncio.wait(
        [
            create_server(rest_api(engines[args.engine]()), args.port),
            create_server(web_GUI(), args.webserver_port),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for pending_task in pending:
        pending_task.cancel("Another service died, server is shutting down")

engines = {"polly": polly, "pyttsx3": pyttsx3, "sapi": sapi,
           "pico": pico, "gctts": gctts, "gtts": gtts, "nsss": nsss}
engines_prettynames = {"Amazon Polly": polly, "pyttsx3": pyttsx3, "Windows SAPI": sapi,
                       "Pico": pico, "Google Cloud Text-To-Speech": gctts, "Google Text-to-Speech": gtts, "NSSpeechSynthesizer": nsss}

if __name__ == "__main__":
    if sys.argv[1] in ["--gui", "-g", "gui", "g"]:
        tkinter_GUI()
    else:
        argparser = argparse.ArgumentParser(prog='pytts',
                                            usage='%(prog)s [options] text',
                                            description="Synthesize text using a range of TTS engines",
                                            epilog='https://benmickler.com/')
        argparser.add_argument('text',
                               metavar='text',
                               type=str,
                               help='the text to be spoken')
        argparser.add_argument('-v',
                               '--verbose',
                               action='store_true',
                               help='print a lot of information, useful for debugging')
        argparser.add_argument('-e',
                               '--engine',
                               type=str,
                               help="the TTS engine/synthesizer to use")
        argparser.add_argument('-ss',
                               '--socket-server',
                               action='store_true',
                               help='run a socket server')
        argparser.add_argument('-sc',
                               '--socket-client',
                               action='store_true',
                               help='run a socket client')
        argparser.add_argument('-rs',
                               '--rest-server',
                               action='store_true',
                               help='run a REST API server')
        argparser.add_argument('-rc',
                               '--rest-client',
                               action='store_true',
                               help='run a REST API client')
        argparser.add_argument('-p',
                               '--port',
                               type=int,
                               help="the port to use for the client/server")
        argparser.add_argument('-wsp',
                               '--webserver-port',
                               type=int,
                               help="the port to use for the web server")
        argparser.add_argument('-i',
                               '--ip',
                               type=str,
                               help="the IP address to use for the client/server")
        argparser.add_argument('-f',
                               '--filename',
                               type=str,
                               help="the name of the file to save the audio to")
        args = argparser.parse_args()
        if not args.engine:
            print("must specify a TTS engine")
        global verbose
        verbose = args.verbose
        if args.socket_client:
            if not args.ip and args.port:
                print("must specify IP and port")
                sys.exit(1)
            asyncio.run(_socket_client(args.text, args.ip, args.port))
        elif args.socket_server:
            if not args.port:
                print("must specify port")
                sys.exit(1)
            asyncio.run(socket_api(engines[args.engine]()).run(args.port))
        elif args.rest_client:
            if not args.ip and args.port:
                print("must specify IP and port")
                sys.exit(1)
            rest_client(args.ip, args.port).speak(args.text)
        elif args.rest_server and args.web_server:
            if not args.port and args.webserver_port:
                print("must specify port")
                sys.exit(1)
            asyncio.run(rest_and_web_servers(args))
        elif args.rest_server:
            if not args.port:
                print("must specify port")
                sys.exit(1)
            uvicorn.run(rest_api(engines[args.engine]()),
                        host="0.0.0.0", port=args.port)
        elif args.web_server:
            if not args.port:
                print("must specify port")
                sys.exit(1)
            uvicorn.run(web_GUI(), host="0.0.0.0", port=args.port)
        else:
            engines[args.engine]().speak(args.text)
