import struct
from numpy.lib.function_base import place
import pvporcupine
import pyaudio
import webrtcvad
import threading
import time
import deepspeech
import numpy as np
import wave
import contextlib
import typing
import asyncio


pa = pyaudio.PyAudio()
FRAMES_PER_BUFFER = 1600
SAMPLE_RATE = 16000

class VoiceActivityMonitor(threading.Thread):
  __is_speaking = False
  __prev_time_spoke = time.time()
  __vad = webrtcvad.Vad()
  __running = True
  __audio_bytes_arr = bytearray()

  def __init__(self, silence_threshold = 1):
    super().__init__()
    self.__vad.set_mode(1)
    self.__silence_threshold = silence_threshold

  
  def callback(self, buff: bytes, buff_len):
    self.__audio_bytes_arr.extend(buff)


  def run(self):
    while self.__running:
      chunk = self.__audio_bytes_arr[:160]
      self.__audio_bytes_arr = self.__audio_bytes_arr[160:]

      while len(chunk) >= 160:
        current_time = time.time()

        if current_time - self.__prev_time_spoke > self.__silence_threshold:
          self.__is_speaking = False

        if self.__vad.is_speech(chunk, SAMPLE_RATE):
          self.__is_speaking = True
          self.__prev_time_spoke = current_time

        chunk = self.__audio_bytes_arr[:160]
    

  def is_speaking(self):
    return self.__is_speaking
  

  def stop(self):
    self.__running = False


class WakewordMonitor(threading.Thread):
  __keywords = ["computer"]
  __audio_bytes = b""
  __porcupine = pvporcupine.create(
    keywords=__keywords
  )

  def __init__(self):
    super().__init__()


  def callback(self, buff):
    self.__audio_bytes = buff


  def run(self):
    self.wait_for_wakeup_word()


  async def wait_for_wakeup_word(self):
    result = -1
    while result == -1:
        while self.__audio_bytes is None:
          await asyncio.sleep(1)
          
        struct = struct.unpack_from("h" * FRAMES_PER_BUFFER, self.__audio_bytes)

        result = self.__porcupine.process(struct)

        if result >= 0:
          print(f"Detected keyword {self.__keywords[result]}")
        
        self.__audio_bytes = None
    

class Recorder(threading.Thread):
  __audio_bytes = b""


  def __init__(self, voice_activity_monitor: VoiceActivityMonitor, data):
    super().__init__()
    self.__vam = voice_activity_monitor
    self.__data = data


  def callback(self, buff):
    self.__audio_bytes = buff


  async def run(self):
    while self.__vam.is_speaking():
      while self.__audio_bytes is None:
        await asyncio.sleep(1)
      
      pcm = self.__audio_stream.read(FRAMES_PER_BUFFER)
      self.__data.writeframes(pcm)
      self.__audio_bytes = None


class PlayBack(threading.Thread):
  def __init__(self, data):
    super().__init__()
    self.__data = data
  

  def run(self):
    stream = pa.open(
      format=pa.get_format_from_width(self.__data.getsampwidth()),
      channels=self.__data.getnchannels(),
      rate=self.__data.getframerate(),
      output=True
    )

    chunk = self.__data.readframes(512)

    while len(chunk) > 0:
      stream.write(chunk)
      chunk = self.__data.readframes(512)

    stream.stop_stream()
    stream.close()



class StreamReader(threading.Thread): 
  __callbacks = []
  
  def __init__(self):
    super().__init__()

  
  def __notify(self, buff, buff_len):
    for callback in self.__callbacks:
      callback(buff, buff_len)
    pass


  def register_callback(self, callback):
    self.__callbacks.append(callback)
    pass


  def deregister_callback(self, callback):
    self.__callbacks.remove(callback)
    pass

  
  def run(self):
    audio_stream = pa.open(
      rate=SAMPLE_RATE,
      channels=1,
      format=pyaudio.paInt16,
      input=True,
      frames_per_buffer=FRAMES_PER_BUFFER,
      input_device_index=pa.get_default_input_device_info()['index']
    )

    while True:
      buff = audio_stream.read(FRAMES_PER_BUFFER)
      self.__notify(buff, FRAMES_PER_BUFFER)
  

class VoiceAssistant(threading.Thread):
  def __init__(self):
    super().__init__()


  def run(self):
    stream_reader = StreamReader()

    vam = VoiceActivityMonitor()
    vam.start()


    wm = WakewordMonitor()
    
    stream_reader.register_callback(vam.callback)
    stream_reader.register_callback(wm.callback)

    while True:
      wm.wait_for_wakeup_word()

      data_in = wave.open("/tmp/voice-assista-temp.wav", "wb")
      data_in.setnchannels(1)
      data_in.setsampwidth(2)
      data_in.setframerate(16000)

      recorder = Recorder(vam, data_in)
      stream_reader.register_callback(recorder.callback)
      recorder.run()

      data_in.close()
      data_out = wave.open("/tmp/voice-assista-temp.wav", "rb")

      playback = PlayBack(data_out)
      playback.run()

      data_out.close()

voice_assistant = VoiceAssistant()
voice_assistant.start()