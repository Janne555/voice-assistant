import struct
from typing import Callable
from numpy.lib.function_base import place
import pvporcupine
import pyaudio
import webrtcvad
import threading
import deepspeech
import numpy as np
import os

from remote_inferrer import RemoteInferrer

SAMPLE_RATE = 16000
MODEL_PATH = "models/deepspeech-0.9.3-models.tflite" if os.uname().machine == 'armv7l' else "models/deepspeech-0.9.3-models.pbmm"
SCORER_PATH = "models/deepspeech-0.9.3-models.scorer"
KEYWORDS = ["computer"]

ds = deepspeech.Model(MODEL_PATH)
ds.enableExternalScorer(SCORER_PATH)

vad = webrtcvad.Vad()
vad.set_mode(1)

porcupine = pvporcupine.create(
  keywords=KEYWORDS
)

def audio_chunks(pcm: bytes, size: int):
  start = 0
  end = size

  chunk = pcm[start:end]

  while len(chunk) == size:
    yield chunk
    
    start = end
    end += size

    chunk = pcm[start:end]


class Listener(threading.Thread):
  def __init__(self, pa: pyaudio.PyAudio, callback: Callable):
    super().__init__()
    self.__audio_stream = pa.open(
      rate=SAMPLE_RATE,
      channels=1,
      format=pyaudio.paInt16,
      input=True,
      input_device_index=pa.get_default_input_device_info()['index']
    )
    self.__callback = callback
    self.__inferrer = RemoteInferrer()


  def run(self):
    while True:
      self.wait_for_wake_word()

      rec_bytes = bytearray()
      ms_since_last_spoke = 0

      self.__callback("listen")

      while ms_since_last_spoke < 1000:
        pcm = self.__audio_stream.read(1600)

        # bytes seem to be double the length of the what is read (2 x int8 -> int16?)
        for chunk in audio_chunks(pcm, 320):
          if vad.is_speech(chunk, SAMPLE_RATE):
            ms_since_last_spoke = 0
          else:
            ms_since_last_spoke += 10

        rec_bytes.extend(pcm)

      self.__callback("inference")
      infered_text = self.__inferrer.infer(rec_bytes)
      self.__callback("command", infered_text)
    

  def wait_for_wake_word(self):
    self.__callback("wait_for_wake_word")
    result = -1
    while result == -1:
      pcm = self.__audio_stream.read(porcupine.frame_length)
      pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

      result = porcupine.process(pcm)

      if result >= 0:
        self.__callback("wakeword", KEYWORDS[result])


if __name__ == "__main__":
  pa = pyaudio.PyAudio()

  def callback(type, *args):
    print(type, *args)


  listener = Listener(pa, callback)
  listener.start()