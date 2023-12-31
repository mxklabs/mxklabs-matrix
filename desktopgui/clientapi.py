from enum import IntEnum

import pathlib
import json

import requests

class Mode(IntEnum):
    OFF         = 0
    ROUND_ROBIN = 1
    SHOW_SLOT   = 2
    LIVE        = 3

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

SERVER_STRING = f"http://{CONFIG['connectToIP4Addr']}:{CONFIG['port']}"
TIMEOUT = CONFIG['api_timeout']

class ClientAPI:
  def __init__(self, base_url=SERVER_STRING):
    self.base_url = base_url
    self.matrix_driver = None

  def clear_slot(self, slot_index : int) -> bool:
    res = requests.delete(f"{self.base_url}/slot/{slot_index}", timeout=TIMEOUT)
    if res.status_code != 200:
      print(res.content)
    return res.status_code == 200

  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    res = requests.post(f"{self.base_url}/slot/{slot_index}", data=gif_data, timeout=TIMEOUT)
    if res.status_code != 200:
      print(res.content)

  def get_slot(self, slot_index : int) -> bytes | None:
    res = requests.get(f"{self.base_url}/slot/{slot_index}", timeout=TIMEOUT)
    if res.status_code == 200:
      return res.content
    if res.status_code == 204:
      return None
    raise RuntimeError(f"Server gave HTTP{res.status_code}: {res.content.decode('utf-8')}")

  def set_live(self, gif_data : bytes) -> bool:
    """ Set a live image. """
    res = requests.post(f"{self.base_url}/live", data=gif_data, timeout=TIMEOUT)
    if res.status_code != 201:
      print(res.content)

  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    res = requests.get(f"{self.base_url}/slot/{slot}", json={"mode": int(mode)}, timeout=TIMEOUT)
    return res.status_code == 200

  def ping(self, ping_id : int) -> int:
    res = requests.get(f"{self.base_url}/ping/{ping_id}", json={"ping_id": int(ping_id)}, timeout=TIMEOUT)
    return res.json()["check_int"]
