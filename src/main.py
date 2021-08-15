from listener import Listener
import pyaudio

pa = pyaudio.PyAudio()

def callback(type, *args):
  print(type, *args)


listener = Listener(pa, callback)
listener.start()