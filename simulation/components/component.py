from typing import List, Optional
from ..item import Item
from ..base import Base

import logging

logger = logging.getLogger(__name__)

class Component(Base):
    _items: List[Optional[Item]]
    
    def __init__(self, capacity: int, name: str = '') -> None:
        super(Component, self).__init__(name=name)

        self._items = [None] * capacity
    
    def _phase_5_commit(self) -> None:
        for i in range(len(self._items) - 1):
            if self._items[i] is None and self._items[i + 1] is not None:
                self._items[i], self._items[i + 1] = self._items[i + 1], self._items[i]
        
        if self._items[-1] is not None:
            return
        
        for i in range(len(self._input)):
            if self._input[i] is None:
                continue
            
            self._items[-1], self._input[i] = self._input[i], None
            assert all(i is None for i in self._input)
            break
    
    def _want_to_send(self) -> bool:
        return self._items[0] is not None
    
    def _has_empty_slot(self) -> bool:
        return None in self._items
    
    def _send_item(self, phase: int = 4) -> None:
        item, self._items[0] = self._items[0], None
        assert item is not None
        self._pending_downstreams[0]._receive_item(self, item)
        logger.debug(f"[PHASE {phase}] \"{self}\" --(\"{item}\")-> \"{self._pending_downstreams[0]}\"")
        self._has_sent_item = True