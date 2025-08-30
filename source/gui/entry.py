class Entry:
    def __init__(self, text, subtext):
        self.subtext = subtext
        self.text = text

    def __str__(self):
        return f"{self.text} ({self.subtext})"


class Entries:
    def __init__(self):
        self.normals = []
        self.specials = []

    def add_normal(self, text, subtext):
        self.normals.append(Entry(text, subtext))

    def add_special(self, text, subtext):
        self.specials.append(Entry(text, subtext))

    def __str__(self):
        return f"{self.name}: {[str(entry) for entry in self.normals]}"