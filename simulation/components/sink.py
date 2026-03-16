from typing import Optional, List, Set

from .base import Component
from ..item import Item


class Sink(Component):
    NEED_ADJUDICATION = False
    
    _received_items: List[Item]
    
    def __init__(self, name: str = '') -> None:
        super(Sink, self).__init__(capacity=1, name=name)
        
        self._received_items = []
    
    def _phase_3_response(self) -> None:
        if self._has_received_item:
            return
        
        assert self._can_accept(None, set())
        
        super(Sink, self)._phase_3_response()
    
    def _phase_4_send(self) -> None:
        if self._has_sent_item:
            return
        
        assert not self._pending_downstreams
    
    def _phase_5_commit(self) -> None:
        self._items[-1], self._input = self._input, None
        if self._items[0] is not None:
            self._received_items.append(self._items[0])
        
        self._reset() 
        
    def _can_accept(self, upstream: Optional[Component], path: Set[Component], phase: int = 3) -> bool:
        return True
        