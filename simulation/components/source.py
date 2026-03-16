from typing import List

from .base import Component
from ..item import Item

import logging

logger = logging.getLogger(__name__)


class Source(Component):
    NEED_ADJUDICATION = False
    
    _rr_index: int
    _item_id:  int
    _sequence: List[str]
    
    def __init__(self, sequence: List[str], name: str = '') -> None:
        super(Source, self).__init__(capacity=1, name=name)
        self._sequence = sequence
        self._rr_index = 0
        self._item_id  = 0
        
        assert self._sequence
        
        self._items[0] = self._get_item()
        self._input    = None

    def _phase_3_response(self) -> None:
        assert not self._has_received_item
        assert not self._pending_upstreams
        
        super(Source, self)._phase_3_response()
        
    def _phase_4_send(self) -> None:
        assert self._rr_index < len(self._sequence)
        
        super(Source, self)._phase_4_send()
    
    # helper methods
    def _get_item(self) -> Item:
        item = Item(self._sequence[self._rr_index], self._item_id)
        self._rr_index = (self._rr_index + 1) % len(self._sequence)
        self._item_id += 1
        
        return item

    def _send_item(self, phase: int = 4) -> None:
        item, self._items[0] = self._items[0], self._get_item()
        
        assert item is not None
        
        self._pending_downstreams[0]._receive_item(item)
        logger.debug(f"[PHASE {phase}] \"{self}\" --(\"{item}\")-> \"{self._pending_downstreams[0]}\"")
        self._has_sent_item = True
    
    def _want_to_send(self) -> bool:
        assert super(Source, self)._want_to_send()
        
        return True