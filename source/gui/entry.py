class GuiEntry:
    def __init__(self, text, delay):
        self.delay = delay
        self.text = text

    def get_text(self):
        return self.text

    def get_subtext(self):
        return f"{self.delay}ms"
    
    def get_delay(self):
        return self.delay

    def __str__(self):
        return f"{self.text} ({self.delay})"
