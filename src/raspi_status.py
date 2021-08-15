from blinker import Blinker

class RaspiStatus():  
  def __init__(self):
    from gpiozero import LED
    self.__led = LED(25)
    self.__blinker = Blinker(self.__led)

  def __clean_up(self):
    self.__blinker.stop()
    self.__blinker = Blinker(self.__led)
    self.__led.off()

  
  def set_blinking(self, speed):
    self.__clean_up()
    self.__blinker.set_speed(speed)
    self.__blinker.start()

  
  def set_off(self):
    self.__clean_up()
    self.__led.off()

  
  def set_on(self):
    self.__clean_up()
    self.__led.on()


if __name__ == "__main__":
  raspi_status = RaspiStatus()