import struct
import pvporcupine
import pyaudio
import webrtcvad
import threading
import time

KEYWORDS = ["computer"]

porcupine = pvporcupine.create(
  keywords=KEYWORDS
)

pa = pyaudio.PyAudio()

wake_word_audio_stream = pa.open(
  rate=porcupine.sample_rate,
  channels=1,
  format=pyaudio.paInt16,
  input=True,
  frames_per_buffer=porcupine.frame_length,
  input_device_index=pa.get_default_input_device_info()['index']
)

class VoiceActivityMonitor(threading.Thread):
  is_speaking = False
  __prev_time_spoke = time.time()
  vad = webrtcvad.Vad()

  def __init__(self):
    super().__init__()
    self.vad.set_mode(1)

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

    while True:
      pcm = audio_stream.read(frames_per_buffer)

      current_time = time.time()

      if current_time - self.__prev_time_spoke > 1:
        self.is_speaking = False

      if self.vad.is_speech(pcm, sample_rate):
        self.is_speaking = True
        self.__prev_time_spoke = current_time
      

vam = VoiceActivityMonitor()
vam.start()

while True:
  pcm = wake_word_audio_stream.read(porcupine.frame_length)
  pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

  result = porcupine.process(pcm)

  if result >= 0:
    print(f"Detected keyword {KEYWORDS[result]}")
    while vam.is_speaking:
      pass
    print(f"speaking stopped")

