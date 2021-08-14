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

pa = pyaudio.PyAudio()

class VoiceActivityMonitor(threading.Thread):
  __is_speaking = False
  __prev_time_spoke = time.time()
  __vad = webrtcvad.Vad()
  __running = True

  def __init__(self, silence_threshold = 1):
    super().__init__()
    self.__vad.set_mode(1)
    self.__silence_threshold = silence_threshold

  def run(self):
    frame_duration = 10
    sample_rate = 16000
    frames_per_buffer = int(sample_rate * frame_duration / 1000)

    audio_stream = pa.open(
      rate=sample_rate,
      channels=1,
      format=pyaudio.paInt16,
      input=True,
      frames_per_buffer=frames_per_buffer,
      input_device_index=pa.get_default_input_device_info()['index'],
    )

    while self.__running:
      pcm = audio_stream.read(frames_per_buffer)

      current_time = time.time()

      if current_time - self.__prev_time_spoke > self.__silence_threshold:
        self.__is_speaking = False

      if self.__vad.is_speech(pcm, sample_rate):
        self.__is_speaking = True
        self.__prev_time_spoke = current_time
    
  def is_speaking(self):
    return self.__is_speaking
  
  def stop(self):
    self.__running = False


class WakewordMonitor(threading.Thread):
  __keywords = ["computer"]

  def __init__(self):
    super().__init__()

  def run(self):
    self.wait_for_wakeup_word()

  def wait_for_wakeup_word(self):
    porcupine = pvporcupine.create(
      keywords=self.__keywords
    )

    audio_stream = pa.open(
      rate=porcupine.sample_rate,
      channels=1,
      format=pyaudio.paInt16,
      input=True,
      frames_per_buffer=porcupine.frame_length,
      input_device_index=pa.get_default_input_device_info()['index']
    )

    result = -1
    while result == -1:
      pcm = audio_stream.read(porcupine.frame_length)
      pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

      result = porcupine.process(pcm)

      if result >= 0:
        print(f"Detected keyword {self.__keywords[result]}")
    


class Recorder(threading.Thread):
  def __init__(self, voice_activity_monitor: VoiceActivityMonitor, data):
    super().__init__()
    self.__vam = voice_activity_monitor
    self.__data = data

  def run(self):
    frames_per_buffer = 512

    audio_stream = pa.open(
      rate=16000,
      channels=1,
      format=pyaudio.paInt16,
      input=True,
      frames_per_buffer=frames_per_buffer,
      input_device_index=pa.get_default_input_device_info()['index']
    )

    while self.__vam.is_speaking():
      pcm = audio_stream.read(frames_per_buffer)
      self.__data.writeframes(pcm)


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


class VoiceAssistant(threading.Thread):
  def __init__(self):
    super().__init__()

  def run(self):
    vam = VoiceActivityMonitor()
    vam.start()

    wm = WakewordMonitor()
    
    while True:
      wm.wait_for_wakeup_word()

      data_in = wave.open("/tmp/voice-assista-temp.wav", "wb")
      data_in.setnchannels(1)
      data_in.setsampwidth(2)
      data_in.setframerate(16000)

      recorder = Recorder(vam, data_in)
      recorder.run()

      data_in.close()
      data_out = wave.open("/tmp/voice-assista-temp.wav", "rb")

      playback = PlayBack(data_out)
      playback.run()

      data_out.close()

voice_assistant = VoiceAssistant()
voice_assistant.start()