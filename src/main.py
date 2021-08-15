from listener import Listener
import pyaudio
import os

pa = pyaudio.PyAudio()

def callback(type, *args):
  print(type, *args)

listener = Listener(pa, callback)
listener.start()