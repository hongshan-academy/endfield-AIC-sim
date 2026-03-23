from typing import Set, Optional, List
from .component import Component
from ..base import Base
from ..item import Item
import logging

logger = logging.getLogger(__name__)


class Converger(Component):
    NEED_ADJUDICATION = True
    
    _rr_index: int
    _selected_upstream: Optional[Base]
    
    def __init__(self, name: str = '') -> None:
        super(Converger, self).__init__(capacity=1, name=name)
            
        self._rr_index = 0
        
    def _phase_2_adjudicate(self) -> None:
        assert not self._has_received_item
        
        for _ in range(len(self._upstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._upstreams)
            upstream = self._upstreams[self._rr_index]
            if upstream in self._pending_upstreams and self._can_accept(upstream, set(), phase=2):
                logger.debug(f"[PHASE 2] \"{self}\" --(select)-> \"{upstream}\" (index={self._rr_index})")
                self._selected_upstream = upstream
                break
        
    def _phase_3_response(self) -> None:
        assert not self._has_received_item

        if self._selected_upstream:
            self._grant(self._selected_upstream)

    def _phase_4_send(self) -> None:        
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        
        self._send_item(phase=4)
        
    def _can_accept(self, upstream: 'Base', path: Set['Base'], phase=3) -> bool:
        # | downstream     | [current]      | behaviour |
        # | -------------- | -------------- | --------- |
        # | ~              | has-empty-slot | grant     |
        # | has-empty-slot | full           | grant     |
        # | full           | full           | recursion |
        
        # cycle detection
        if self in path:
            logger.debug(f"[PHASE {phase}] \"{self}\" detects cycle in path {path}")
            # this should not be cached
            return False
        
        if self._can_accept_cache.get(upstream) is not None:
            if self._can_accept_cache[upstream]:
                logger.debug(f"[PHASE {phase}] \"{self}\" --(can accept)-> \"{upstream}\" (cached)")
            else:
                logger.debug(f"[PHASE {phase}] \"{self}\" --(cannot accept)-> \"{upstream}\" (cached)")
                
            return self._can_accept_cache[upstream]
        
        if upstream != self._upstreams[self._rr_index]:
            self._can_accept_cache[upstream] = False
            return False
        
        path.add(self)
        
        if self._has_empty_slot():
            self._can_accept_cache[upstream] = True
        else:
            self._can_accept_cache[upstream] = any(
                downstream._can_accept(self, path, phase) for downstream in self._downstreams
            )
        
        path.remove(self)
        
        if self._can_accept_cache[upstream]:
            logger.debug(f"[PHASE {phase}] \"{self}\" --(can accept)-> \"{upstream}\"")
        else:
            logger.debug(f"[PHASE {phase}] \"{self}\" --(cannot accept)-> \"{upstream}\"")
            
        return self._can_accept_cache[upstream]

    def _reset(self) -> None:
        super(Converger, self)._reset()
        
        self._selected_upstream = None