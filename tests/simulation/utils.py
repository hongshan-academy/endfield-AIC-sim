from typing import List, Tuple
from simulation.components.component import Component
from simulation import Base


def trace_id(components: List[Base]) -> Tuple:
    return tuple(
        tuple((item.id + 1) if item else 0 for item in component._items) 
        for component in components if isinstance(component, Component)
    )
    
def trace_bool(components: List[Base]) -> Tuple:
    return tuple(
        tuple(1 if item else 0 for item in component._items) 
        for component in components if isinstance(component, Component)
    )
    
def trace_type(components: List[Base]) -> Tuple:
    return tuple(
        tuple(item.type if item else '_' for item in component._items) 
        for component in components if isinstance(component, Component)
    )