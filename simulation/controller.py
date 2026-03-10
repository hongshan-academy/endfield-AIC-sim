from typing import Dict, Set, Optional

from components import Component, Source


class Controller(object):
    def __init__(self, components: Dict[Component, Component]) -> None:
        self._components = components
    
    def step(self) -> None:
        for component in self._components:
            if isinstance(component, Source):
                component._phase_1_request()
        
        for component in self._components:
            component._phase_2_response()
        
        for component in self._components:
            component._phase_3_send()
        
        for component in self._components:
            component._phase_4_commit()