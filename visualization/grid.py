from typing import Tuple

from .wrapper import PlacedComponent

class Grid(object):
    def __init__(self, shape: Tuple[int, int], components: PlacedComponent) -> None:
        self.shape = shape
        
    def link(self):
        pass