class GuiEntry:
    def __init__(self, text, delay, color, acolor, special=False):
        self.delay = delay
        self.text = text
        self.color = color
        self.acolor = acolor
        self.special = special

    def get_special(self):
        return self.special

    def get_color(self):
        return self.color

    def get_acolor(self):
        return self.acolor

    def get_text(self):
        return self.text

    def get_subtext(self):
        return f"{self.delay}ms"

    def get_delay(self):
        return self.delay

    def __str__(self):
        return f"{self.text} ({self.delay})"
