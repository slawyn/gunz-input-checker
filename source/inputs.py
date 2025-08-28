import source.utils as utils


class Input:
    def __init__(self, key, delay):
        self.key = key
        self.delay = delay

    def get_key(self):
        return self.key

    def get_delay(self):
        return self.delay

    def __str__(self):
        return f"{self.key:6}({self.delay:3})"


class MoveInput():
    def __init__(self, accepted_keys, max_delay, min_delay):
        self.keys = accepted_keys.split("|")
        self.max_delay = max_delay
        self.min_delay = min_delay

    def get_first_key(self):
        return self.keys[0]

    def get_min_delay(self):
        return self.min_delay

    def is_executed(self, input):
        return (self.min_delay <= input.delay <= self.max_delay) and input.key in self.keys

    def __str__(self):
        return f"{self.keys}({self.min_delay}-{self.max_delay:3})"


class Move:
    def __init__(self, name, inputs=[]):
        self.name = name
        self.inputs = inputs
        self.next = 0
        self.accumulated_delay = 0

    def has_inputs(self):
        return len(self.inputs) > 0

    def get_inputs(self):
        return self.inputs

    def execute(self, input):
        if self.next == 0:
            if self.inputs[0].is_executed(input):
                self.accumulated_delay = 0
                self.next += 1
                return True
            return False

        elif self.next < len(self.inputs) and self.inputs[self.next].is_executed(input):
            self.next += 1
            self.accumulated_delay += input.delay
            return True
        else:
            self.next = 0
            return self.execute(input)

    def get_accumulated_delay(self):
        return self.accumulated_delay

    def is_executed(self):
        return self.next == len(self.inputs)

    def reset(self):
        self.next = 0

    def __str__(self):
        out = self.name + ":\n"
        out += " + ".join([str(input) for input in self.inputs])
        return out


class AutomatedMove:

    def __init__(self, name, inputs=[]):
        self.name = name
        self.inputs = inputs
        self.timestamp = 0
        self.executed = 0
        self.pressed = False

    def can_be_executed(self, ts):
        return self.timestamp + self.inputs[self.executed].min_delay < ts

    def get_next_input_key(self):
        return self.inputs[self.executed].get_first_key()

    def set_pressed(self, timestamp):
        self.pressed = True
        self.timestamp = timestamp

    def set_released(self):
        self.pressed = False
        self.executed += 1

    def needs_releasing(self, ts):
        return self.pressed and (ts - self.timestamp) > utils.get_random(50, 100)

    def is_pressed(self):
        return self.pressed

    def is_done(self):
        return self.executed == len(self.inputs)


class InputBuffer:

    def __init__(self):
        self.name = ""
        self.pending = []
        self.timestamp = 0

    def add(self, key, ts):
        delay = ts - self.timestamp
        self.timestamp = ts
        self.pending.append(Input(key, delay))

    def pop_input(self):
        if self.pending:
            return self.pending.pop(0)
        return []

    def is_move_executed(self, input, move):
        if move.execute(input):
            if move.is_executed():
                move.reset()
                return True

        return False

    def __str__(self):
        return " + ".join([str(input) for input in (self.pending)])
