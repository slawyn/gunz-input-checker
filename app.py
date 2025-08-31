import threading
import sys
from pynput import keyboard, mouse
from glob import glob

from source.inputs import InputBuffer, AutomatedMove, Move, MoveInput, Input
from source.gui.gui import GuiApplication
from source.gui.gui import GuiHandler
from source.gui.entry import GuiEntry 
import source.utils as utils

class MappedInput:
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

    def get_colors(self):
        return list(self.action2color_map.values())

    def _resolve_action_color(self, action):
        if action in self.action2color_map:
            return self.action2color_map[action]
        return "#FFFFFF"

    def find_move(self, name):
        for move in self.moves:
            if move.name == name:
                return move

    def run(self):
        ts = utils.get_timestamp_ms()
        self.process_automated(ts)
        return self.process_manual(ts)

    def create_entries(self, original, derived):
        inputs = []
        outputs = []
        for input in original:
            action = input.get_action()
            inputs.append(GuiEntry(action,input.get_delay(), self._resolve_action_color(action)))

        for input in derived:
            action = input.get_action()
            outputs.append(GuiEntry(action, input.get_delay(), self._resolve_action_color(action)))

        clear = self.clear 
        if self.clear:
            self.clear = False
        return inputs, outputs, clear, self.running

    def process_manual(self, ts):
        original = []
        derived = []
        if input := self.buffer.pop():
            original.append(input)
            for move in self.moves:
                if self.buffer.is_move_executed(input, move):
                    self.moves_counter += 1
                    derived.append(Input(f"[{self.moves_counter}]{move.name}", move.get_accumulated_delay()))

        return self.create_entries(original, derived)

    def process_automated(self, ts):
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



    def handle(self, key):
        ts = utils.get_timestamp_ms()
        if key in self.key2action_map:
            self.buffer.add(self.key2action_map[key], ts)
        else:
            print(ts, key)
            # if key == "+":
            #     self.automated_input = AutomatedMove("Automated", self.find_move("Reloadshot").inputs)

        if key == "+":
            self.buffer.clear()
            self.clear = True

        if key == "-":
            self.running = False

    def on_press(self, key):
        self.handle(key.char if hasattr(key, 'char') and key.char else key)
        return self.running

    def on_release(self, key):
        return self.running

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.handle(button)
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
            move = Move(name, [MoveInput(input["input"], input["max.delay"] if "max.delay" in input else 2**33, input["min.delay"] if "min.delay" in input else 0) for input in values])
            moves.append(move)
            print(move)

    return moves


if __name__ == "__main__":
    mappings = {
        "w": MappedInput("↑", "#FF9000"),
        "a": MappedInput("←", "#FF9000"),
        "s": MappedInput("↓", "#FF9000"),
        "d": MappedInput("→", "#FF9000"),
        "e": MappedInput("W1", "#036FFC"),
        "q": MappedInput("W2", "#1100FF"),
        keyboard.Key.space: MappedInput("R", "#FF1500"),
        keyboard.Key.caps_lock: MappedInput("S", "#FFFFFF"),
        mouse.Button.left: MappedInput("A", "#00A31B"),
        mouse.Button.right: MappedInput("J", "#FF00AA"),
        mouse.Button.x2: MappedInput("B", "#A7A7A7"),
        mouse.Button.middle: MappedInput("G", "#D268FF"),
    }


    # Start keyboard and mouse listeners in separate threads
    handler = Handler(mappings, load_moves(glob('moves/**/*.json', recursive=True)))
    keyboard_thread = threading.Thread(target=start_keyboard_listener, args=(handler,))
    mouse_thread = threading.Thread(target=start_mouse_listener, args=(handler,))
    keyboard_thread.start()
    mouse_thread.start()

    app = GuiApplication(sys.argv, handler, handler.get_colors())
    app.start()

    keyboard_thread.join()
    mouse_thread.join()
