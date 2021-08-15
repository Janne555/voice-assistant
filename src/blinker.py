
import threading
import asyncio

class Blinker(threading.Thread):
  __is_running = True

  def __init__(self, led, speed):
    super().__init__()
    self.__led = led
    self.__speed = speed

  
  async def run(self):
    self.__is_running = True
    led_on = False
    while self.__is_running:
      led_on = not led_on
      if (led_on):
        self.__led.off()
      else:
        self.__led.on()
      await asyncio.sleep(self.__speed)


  def stop(self):
    self.__is_running = False


if __name__ == "__main__":
  from gpiozero import LED
  led = LED(23)
  blinker = Blinker(led, 500)
  blinker.start()