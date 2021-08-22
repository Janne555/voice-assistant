import socket
from collections import namedtuple
import struct
from enum import IntEnum
import os

print("foo", os.getenv("INFERRER_TCP_IP"), os.getenv("INFERRER_TCP_PORT"))


Message = namedtuple("Message", "type length data")

class MessageType(IntEnum):
  AUDIO_START = 0
  AUDIO_END = 1
  AUDIO_DATA = 2
  INFERRED_START = 3
  INFERRED_DATA = 4
  INFERRED_END = 5

TCP_IP = os.getenv("INFERRER_TCP_IP")
TCP_PORT = int(os.getenv("INFERRER_TCP_PORT"))

class RemoteInferrer():
  def __init__(self) -> None:
    self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.__socket.connect((TCP_IP, TCP_PORT))
    pass


  def infer(self, data: bytearray):
    self.__socket.send(struct.pack("BH1020s", MessageType.AUDIO_START, 0, b""))
    
    for i in range(0, len(data), 1020):
      chunk = data[i:i+1020]
      self.__socket.send(struct.pack("BH1020s", MessageType.AUDIO_DATA, len(chunk), chunk))
    
    self.__socket.send(struct.pack("BH1020s", MessageType.AUDIO_END, 0, b""))

    inferred_text = ""

    while True:
      data = self.__socket.recv(1024)

      unpacked = struct.unpack("BH1020s", data)
      message = Message._make(unpacked)
      if (message.type == MessageType.INFERRED_END):
        break
      if (message.type == MessageType.INFERRED_DATA):
        inferred_text += str(message.data, "utf-8")

    return inferred_text