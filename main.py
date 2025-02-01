import threading
import sys
import os
from pynput import keyboard, mouse
from glob import glob

from inputs import InputBuffer, AutomatedMove, Move, MoveInput
from gui import Application, Entries
import utils


class Handler:
    def __init__(self, mappings, moves):
        self.running = True
        self.mappings = mappings
        self.reverse_mappings = {v: k for k, v in mappings.items()}
        self.moves = moves
        self.buffer = InputBuffer("")
        self.buffer.reset()
        self.available_moves = self.moves[:]
        self.automated_input = None
        self.kb_controller = keyboard.Controller()
        self.ms_controller = mouse.Controller()

    def find_move(self, name):
        for move in self.moves:
            if move.name == name:
                return move

    def run(self):
        ts = utils.get_timestamp_ms()
        if self.buffer.has_inputs():
            entries = Entries()
            for input in self.buffer.get_inputs():
                entries.add(input.get_key(), str(input.get_delay()))

            is_input_correct = False
            for move in self.moves:
                if move in self.available_moves:
                    status = self.buffer.is_input_correct(move)
                    if status == InputBuffer.MOVE:
                        self.available_moves.remove(move)
                        is_input_correct = True
                        entries.set_name(move.name)
                    elif status == InputBuffer.ACCEPTED:
                        is_input_correct = True
                    else:
                        self.available_moves.remove(move)

            if not is_input_correct:
                self.buffer.reset()
                self.available_moves = self.moves[:]
            else:
                self.buffer.accept()

            return entries

        # Can any moves still be executed?
        is_time_remaining = False
        for move in self.moves:
            if move in self.available_moves and self.buffer.is_time_remaining(ts, move):
                is_time_remaining = True
            else:
                move.reset()

        if not is_time_remaining:
            self.buffer.reset()
            self.available_moves = self.moves[:]

        if self.automated_input:
            if self.automated_input.is_done():
                self.automated_input = None
            elif self.automated_input.is_pressed():
                if self.automated_input.needs_releasing(ts):
                    key = self.reverse_mappings[self.automated_input.get_next_input_key()]
                    if type(key) == mouse.Button:
                        self.ms_controller.release(key)
                    else:
                        self.kb_controller.release(key)
                    self.automated_input.set_released()
            elif self.automated_input.can_be_executed(ts):
                key = self.reverse_mappings[self.automated_input.get_next_input_key()]
                if type(key) == mouse.Button:
                    self.ms_controller.press(key)
                else:
                    self.kb_controller.press(key)
                self.automated_input.set_pressed(ts)

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def handle(self, key):
        ts = utils.get_timestamp_ms()
        if key in self.mappings:
            self.buffer.add(self.mappings[key], ts)
        else:
            print(ts, key)
            if key == "+":
                self.automated_input = AutomatedMove("Automated",
                                                     self.find_move("Reloadshot").inputs)

        if key == keyboard.Key.esc:
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
            move = Move(name, [MoveInput(input["input"], input["max.delay"], input["min.delay"] if "min.delay" in input else 0) for input in values])
            moves.append(move)

    for move in moves:
        print(move.name)
        for input in move.inputs:
            print(f"  {input}")
    return moves


if __name__ == "__main__":
    mappings = {
        "w": "↑",
        "a": "←",
        "s": "↓",
        "d": "→",
        "e": "W1",
        "q": "W2",
        keyboard.Key.space: "R",
        keyboard.Key.caps_lock: "S",
        mouse.Button.left: "A",
        mouse.Button.right: "Jump",
        mouse.Button.x2: "B",
        mouse.Button.middle: "G"
    }

    # Start keyboard and mouse listeners in separate threads
    handler = Handler(mappings, load_moves(glob('moves/**/*.json', recursive=True)))
    keyboard_thread = threading.Thread(target=start_keyboard_listener, args=(handler,))
    mouse_thread = threading.Thread(target=start_mouse_listener, args=(handler,))
    keyboard_thread.start()
    mouse_thread.start()

    app = Application(sys.argv, handler)
    app.start()

    keyboard_thread.join()
    mouse_thread.join()
