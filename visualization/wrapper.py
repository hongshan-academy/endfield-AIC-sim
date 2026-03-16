from typing import Tuple, Union

from simulation import Component

from .enum import Direction
from simulation import *

class PlacedComponent(object):
    location: Tuple[int, int]
    direction: Direction
    
    def __init__(
        self, 
        component: Union[Source, Sink, Splitter, Converger, Conveyor], 
        location: Tuple[int, int], 
        direction: Direction
    ) -> None:
        self.component = component
        self.location = location
        self.direction = direction
    
class PlacedConveyer(object):
    trace: Tuple[int, int, int, int]
    component: Conveyor
    
    def __init__(self, trace: Tuple[int, int, int, int], length: int) -> None:
        self.trace = trace
        self.component = Conveyor(capacity=length, name=f'Conveyor{trace}')
