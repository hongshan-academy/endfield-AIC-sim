from simulation import Base, Component, Unit
from simulation import Controller
from simulation import Converger, Conveyor, Sink, Source, Splitter
# from simulation import StorageBox


class Priority(Component):
    def __init__(self, capacity: int, name: str = '') -> None:
        super().__init__(capacity, name)