from typing import Dict, Set, Optional

from .components import Component, Source


class Controller(object):
    _mapping: Dict[str, str]
    
    def __init__(self, mapping: Dict[str, str]) -> None:
        self._mapping = mapping
        self._components = []
    
    def step(self) -> None:
        for component in self._components:
            if isinstance(component, Source):
                component._phase_1_request()
                    
        for component in self._components:
            component._phase_2_adjudicate()
        
        for component in self._components:
            component._phase_3_response()
        
        for component in self._components:
            component._phase_4_send()
        
        for component in self._components:
            component._phase_5_commit()