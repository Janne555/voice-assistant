from listener import Listener
import pyaudio
import os
from raspi_status import RaspiStatus

is_raspi = os.uname().machine == 'armv7l'

pa = pyaudio.PyAudio()

def callback(m_type, *args):
  print(m_type, *args)

def make_raspi_callback():
  raspi_status = RaspiStatus()

  def raspi_callback(m_type, *args):
    print(m_type, *args)
    if m_type == "wait_for_wake_word":
      raspi_status.set_blinking(600)
    elif m_type == "listen":
      raspi_status.set_on()
    elif m_type == "inference":
      raspi_status.set_blinking(300)

  return raspi_callback


listener = Listener(pa, make_raspi_callback() if is_raspi else callback)
listener.start()