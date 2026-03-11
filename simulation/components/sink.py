from typing import Optional, List, Set

from .base import Component
from ..item import Item


class Sink(Component):
    _received_items: List[Item]
    
    def __init__(self, name: str = '') -> None:
        super(Sink, self).__init__(capacity=1, name=name)
        
        self._received_items = []
    
    def _phase_3_response(self) -> None:
        assert self._can_accept(None, set())
        
        super(Sink, self)._phase_3_response()
    
    def _phase_4_send(self) -> None:
        assert not self._pending_downstreams
    
    def _phase_5_commit(self) -> None:
        self._items[-1], self._input = self._input, None
        if self._items[0] is not None:
            self._received_items.append(self._items[0])      
        self._reset()
        
    def _can_accept(self, upstream: Optional[Component], path: Set[Component]) -> bool:
        return True
        