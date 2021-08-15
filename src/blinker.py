
import threading
import time

class Blinker(threading.Thread):
  __is_running = True
  __speed = 500

  def __init__(self, led):
    super().__init__()
    self.__led = led


  def set_speed(self, speed):
    self.__speed = speed

  
  def run(self):
    self.__is_running = True
    led_on = False
    while self.__is_running:
      led_on = not led_on
      if (led_on):
        self.__led.off()
      else:
        self.__led.on()
      
      time.sleep(self.__speed / 1000)


  def stop(self):
    self.__is_running = False


if __name__ == "__main__":
  from gpiozero import LED
  led = LED(25)
  blinker = Blinker(led, 25)
  blinker.start()