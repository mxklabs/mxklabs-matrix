import json
import pathlib
import os
import shutil

from typing import TYPE_CHECKING, Union, Mapping, List, Tuple, Dict

from observable import Observable

if TYPE_CHECKING:
    Json = Union[str, int, float, bool, None, Mapping[str, 'Json'], List['Json']]

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class StateHandler:
    """ Interface for classes that deal with state. """

    def go_black(self) -> None:
        """ Make the screen go black. """
        ...

    def go_live(self) -> None:
        """ Go into a live mode. """
        ...

    def go_slot(self, slot : int) -> None:
        """ Display a specific slot. """
        ...

    def go_round_robin(self) -> None:
        """ Display all slots in a round robin fashion. """
        ...


class StateManager(StateHandler, Observable):
    """ Class that handles state changes. """

    def __init__(self, state_handler : StateHandler):
        """ Initialise. """
        Observable.__init__(self)
        self._state_handler = state_handler
        self._state_json = json.dumps({ "mode" : "black"})

        # Add an observer that prints the state when it changes.
        self.add_observer(lambda: print(f"State: {self._state_json}", flush=True)))

    def go_black(self) -> None:
        """ Make the screen black.
            Also: remember the state and tell observers. """
        self._state_handler.go_black()
        self._update_state({ "mode" : "black"})

    def go_live(self) -> None:
        """ Make the screen go live.
            Also: remember the state and tell observers. """
        self._state_handler.go_live()
        self._update_state({ "mode" : "live"})

    def go_slot(self, slot : int) -> None:
        """ Make the screen display a specific slot.
            Also: remember the state and tell observers. """
        self._state_handler.go_slot(slot)
        self._update_state({ "mode" : "slot", "slot" : slot})

    def go_round_robin(self) -> None:
        """ Make the screen all slots in a round robin fashion.
            Also: remember the state and tell observers. """
        self._state_handler.go_round_robin()
        self._update_state({ "mode" : "round_robin"})

    def is_black(self) -> bool:
        """ Return True if we're black. """
        return self._check_mode("black")

    def is_live(self) -> bool:
        """ Return True if we're live. """
        return self._check_mode("live")

    def is_round_robin(self) -> bool:
        """ Return True if we're round_robin. """
        return self._check_mode("round_robin")

    def is_slot(self) -> Tuple[bool, int]:
        """ Return True, slot if we're in slot mode. """
        res = self._check_mode("slot")
        if not res:
            return False, 0
        else:
            dic = json.loads(self._state_json)
            if "slot" not in dic:
                raise RuntimeError(f"Invalid json: {self._state_json}")
            return True, dic["slot"]

    def json(self):
        """ Get a json representation of the state. """
        return self._state_json

    def visit(self, json_data : 'Json'=None, state_handler : StateHandler=None) -> None:
        """ Action state from json."""
        if json_data is None:
            json_data = self._state_json
        if state_handler is None:
            state_handler = self

        dic = json.loads(json_data)
        if "mode" not in dic:
            raise RuntimeError(f"Invalid json: {json_data}")

        match dic["mode"]:
            case "black":
                self.go_black()
            case "slot":
                if "slot" not in dic:
                    raise RuntimeError(f"Invalid json: {json_data}")
                self.go_slot(dic["slot"])
            case "round_robin":
                self.go_round_robin()
            case "live":
                self.go_live()
            case _:
                raise RuntimeError(f"Invalid json: {json_data}")

    def _update_state(self, new_state : Dict):
        """ Internal method to update state. """
        old_json = self._state_json
        self._state_json = json.dumps(new_state)
        if old_json != self._state_json:
            self._notify_observers()

    def _check_mode(self, mode_str : str):
        """ Return true mode matches. """
        dic = json.loads(self._state_json)
        if "mode" not in dic:
            raise RuntimeError(f"Invalid json: {self._state_json}")
        return dic["mode"] == mode_str



class FileBackedStateSaver:
    """ Class that saves state to a file when it changes. """

    def __init__(self, state_manager : StateManager):
        self._state_manager = state_manager

        self.SLOT_DATA_DIR = pathlib.Path(CONFIG['slotDataDir'])
        self.SLOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.chown(self.SLOT_DATA_DIR, user=CONFIG['user'], group=CONFIG['group'])
        os.chmod(self.SLOT_DATA_DIR, 0o777)

    def notify(self):
        """ Do the saving. """
        with open(self.SLOT_DATA_DIR / "state.json", "w") as f:
            f.write(self._state_json)
