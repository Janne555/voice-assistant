
import threading

from blinker import Blinker

class RaspiStatus(threading.Thread):
  __status = "off"
  
  def __init__(self):
    super().__init__()
    from gpiozero import LED
    self.__led = LED(23)
  
  def run(self):
    blinker = Blinker(self.__led)

    while True:
      if (self.__status == "blink"):
        blinker.start()
      else:
        blinker.stop()


if __name__ == "__main__":
  raspi_status = RaspiStatus()
  raspi_status.start()