from typing import List, Set

from .base import Component
from ..item import Item


class Sink(Component):
    _received_items: List[Item]
    
    def __init__(self, name: str = '') -> None:
        super(Sink, self).__init__(capacity=1, name=name)
        self._received_items = []
    
    def _phase_2_response(self) -> None:
        assert self._can_accept(set())
        
        super(Sink, self)._phase_2_response()
    
    def _phase_3_send(self) -> None:
        assert not self._pending_downstreams
    
    def _phase_4_commit(self) -> None:
        self._items[-1], self._input = self._input, None      
        self._reset()
        
    def _can_accept(self, path: Set[Component]) -> bool:
        return True