# core/net.py
class Net:
    def __init__(self, name: str):
        self.name = name
        self.pins = []

    def connect(self, pin):
        self.pins.append(pin)
        pin.net = self
