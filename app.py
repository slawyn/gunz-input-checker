import threading
import sys
from pynput import keyboard, mouse
from glob import glob

from source.inputs import InputBuffer, AutomatedMove, Move, MoveInput, Input
from source.gui.gui import GuiApplication
from source.gui.gui import GuiHandler
from source.gui.entry import GuiEntry
import source.utils as utils


class Mapped:
    def __init__(self, action, color):
        self.action = action
        self.color = color

    def get_action(self):
        return self.action

    def get_color(self):
        return self.color


class Handler(GuiHandler):
    def __init__(self, map, moves):
        self.running = True
        self.key2action_map = {k: v.get_action() for k, v in map.items()}
        self.action2color_map = {v.get_action(): v.get_color() for v in map.values()}
        self.action2key_map = {v.get_action(): k for k, v in map.items()}
        self.moves = moves
        self.buffer = InputBuffer()
        self.available_moves = self.moves[:]
        self.automated_input = None
        self.kb_controller = keyboard.Controller()
        self.ms_controller = mouse.Controller()
        self.moves_counter = 0
        self.clear = False

    def run(self):
        ts = utils.get_timestamp_ms()
        self._process_automated(ts)
        return self._process_manual(ts)

    def _get_available_colors(self):
        return list(self.action2color_map.values()) + ["#19EEE7"]

    def _resolve_action_color(self, action):
        if action in self.action2color_map:
            return self.action2color_map[action]
        return "#19EEE7"

    def _find_move(self, name):
        for move in self.moves:
            if move.name == name:
                return move

    def _create_gui_entries(self, inputs):
        entries = []
        for input in inputs:
            action = input.get_action()
            entries.append(GuiEntry(action, input.get_delay(),
                           self._resolve_action_color(action), special=input.is_derived()))

        clear = self.clear
        if self.clear:
            self.clear = False
        return entries, clear, self.running

    def _process_manual(self, ts):
        inputs = []
        if input := self.buffer.pop():
            inputs.append(input)
            for move in self.moves:
                if move.is_executed(input):
                    self.moves_counter += 1
                    inputs.append(Input(f"[{move.get_accumulated_delay()}]{move.name}", 1, derived=True))

        return self._create_gui_entries(inputs)

    def _process_automated(self, ts):
        if self.automated_input:
            if self.automated_input.is_done():
                self.automated_input = None
            elif self.automated_input.is_pressed():
                if self.automated_input.needs_releasing(ts):
                    key = self.action2key_map[self.automated_input.get_next_input_key()]
                    if type(key) == mouse.Button:
                        self.ms_controller.release(key)
                    else:
                        self.kb_controller.release(key)
                    self.automated_input.set_released()
            elif self.automated_input.can_be_executed(ts):
                key = self.action2key_map[self.automated_input.get_next_input_key()]
                if type(key) == mouse.Button:
                    self.ms_controller.press(key)
                else:
                    self.kb_controller.press(key)
                self.automated_input.set_pressed(ts)

    def _handle_key(self, key):
        ts = utils.get_timestamp_ms()
        if key in self.key2action_map:
            self.buffer.add(self.key2action_map[key], ts)
        else:
            print(ts, key)

        if key == "+":
            self.buffer.clear()
            self.clear = True

        if key == "-":
            self.running = False

        if key == "*":
            self.automated_input = AutomatedMove("Automated", self._find_move("Reloadshot").inputs)

    def on_press(self, key):
        self._handle_key(key.char if hasattr(key, 'char') and key.char else key)
        return self.running

    def on_release(self, key):
        return self.running

    def on_click(self, x, y, button, pressed):
        if pressed:
            self._handle_key(button)
        return self.running


def start_keyboard_listener(handler):
    with keyboard.Listener(on_press=handler.on_press, on_release=handler.on_release) as listener:
        listener.join()


def start_mouse_listener(handler):
    with mouse.Listener(on_click=handler.on_click) as listener:
        listener.join()


def load_moves(filenames):
    moves = []
    for filename in filenames:
        print(filename)
        for name, values in utils.load_json(filename).items():
            move = Move(name, [MoveInput(input["input"],
                                         input["max.delay"] if "max.delay" in input else 2 ** 33,
                                         input["min.delay"] if "min.delay" in input else 0)
                               for input in values])
            moves.append(move)
            print(move)

    return moves


if __name__ == "__main__":
    mappings = {
        "w": Mapped("↑", "#FF9000"),
        "a": Mapped("←", "#FF9000"),
        "s": Mapped("↓", "#FF9000"),
        "d": Mapped("→", "#FF9000"),
        "e": Mapped("W1", "#036FFC"),
        "q": Mapped("W2", "#1100FF"),
        keyboard.Key.space: Mapped("R", "#FF1500"),
        keyboard.Key.caps_lock: Mapped("S", "#FFFFFF"),
        mouse.Button.left: Mapped("A", "#00A31B"),
        mouse.Button.right: Mapped("J", "#FF00AA"),
        mouse.Button.x2: Mapped("B", "#A7A7A7"),
        mouse.Button.middle: Mapped("G", "#D268FF"),
    }

    # Start keyboard and mouse listeners in separate threads
    handler = Handler(mappings, load_moves(glob('moves/**/*.json', recursive=True)))
    keyboard_thread = threading.Thread(target=start_keyboard_listener, args=(handler,))
    mouse_thread = threading.Thread(target=start_mouse_listener, args=(handler,))
    keyboard_thread.start()
    mouse_thread.start()

    app = GuiApplication(sys.argv, handler, handler._get_available_colors())
    app.start()

    keyboard_thread.join()
    mouse_thread.join()
