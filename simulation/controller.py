from typing import List

from .components import Component, Source


class Controller(object):
    _components: List[Component]
    
    def __init__(self, components: List[Component]) -> None:
        self._components = components
    
    def step(self) -> None:
        for component in self._components:
            component._phase_1_request()
                    
        for component in self._components:
            component._phase_2_adjudicate()
        
        for component in self._components:
            component._phase_3_response()
        
        for component in self._components:
            component._phase_4_send()
        
        for component in self._components:
            component._phase_5_commit()

def run_simulation(components: List[Component], total_ticks: int):
    controller = Controller(components)
    for _ in range(total_ticks):
        controller.step()
    