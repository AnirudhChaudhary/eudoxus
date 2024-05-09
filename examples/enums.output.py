class Enumeration(Module):
    def types(self):
        self.Color = Enum("red", "green", "blue")
        self.Other = Enum("r", "g", "b")
        self.Other2 = Enum("anon_enum_0", "anon_enum_1", "anon_enum_2", "anon_enum_3")
        self.Other3 = Enum("anon_enum_4")

    def locals(self):
        self.color = self.Color

    def init(self):
        self.color = "red"

    def next(self):
        self.color = "green"

    def specification(self):
        return self.color != "blue"