from typing import List, Tuple
from simulation import Component


def trace_id(components: List[Component]) -> Tuple:
    return tuple(
        tuple((item.id + 1) if item else 0 for item in component._items) 
        for component in components
    )
    
def trace_bool(components: List[Component]) -> Tuple:
    return tuple(
        tuple(1 if item else 0 for item in component._items) 
        for component in components
    )