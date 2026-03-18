from typing import List

from .components import Component, Source


class Controller(object):
    _components: List[Component]
    
    def __init__(self, components: List[Component]) -> None:
        self._components = components
    
    def step(self) -> None:
        for component in self._components:
            component.phase_1_tick()
                    
        for component in self._components:
            component.phase_2_tick()
        
        for component in self._components:
            component.phase_3_tick()
        
        for component in self._components:
            component.phase_4_tick()
        
        for component in self._components:
            component.phase_5_tick()

def run_simulation(components: List[Component], total_ticks: int):
    controller = Controller(components)
    for _ in range(total_ticks):
        controller.step()
    