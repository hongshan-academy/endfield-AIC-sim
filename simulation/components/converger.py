from typing import Set, Optional
from .base import Component
import logging

logger = logging.getLogger(__name__)


class Converger(Component):
    _rr_index: int
    
    def __init__(self, name: str = '') -> None:
        super(Converger, self).__init__(capacity=1, name=name)
        
        self._rr_index = 0
    
    def _phase_2_response(self) -> None:
        if not self._pending_upstreams:
            return
        
        for _ in range(len(self._upstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._upstreams)
            upstream = self._upstreams[self._rr_index]
            if upstream in self._pending_upstreams:
                logger.debug(f"[PHASE 2] {self} grants {upstream}")
                self._grant(upstream)
                break

    def _phase_3_send(self) -> None:        
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        
        if self._pending_downstreams:
            logger.debug(f"[PHASE 3] {self} sends {self._items[0]} to {self._pending_downstreams[0]}")
            self._pending_downstreams[0]._input, self._items[0] = self._items[0], None
        
    def _can_accept(self, upstream: 'Component', path: Set['Component']) -> bool:
        # | downstream     | [current]      | behaviour |
        # | -------------- | -------------- | --------- |
        # | ~              | has-empty-slot | grant     |
        # | has-empty-slot | full           | grant     |
        # | full           | full           | recursion |
        
        # cycle detection
        if self in path:
            logger.debug(f"[PHASE 2] {self} detects cycle in path {path}")
            # this should not be cached
            return False
        
        if self._can_accept_cache.get(upstream) is not None:
            logger.debug(f"[PHASE 2] {self} can accept from {upstream} (cached)")
            return self._can_accept_cache[upstream]
        
        if upstream == self._upstreams[self._rr_index]:
            self._can_accept_cache[upstream] = False
            return False
        
        path.add(self)
        
        if self._has_empty_slot():
            self._can_accept_cache[upstream] = True
        else:
            self._can_accept_cache[upstream] = any(
                downstream._can_accept(self, path) for downstream in self._downstreams
            )
        
        path.remove(self)
        
        if self._can_accept_cache[upstream]:
            logger.debug(f"[PHASE 2] {self} can accept from {upstream}")
        else:
            logger.debug(f"[PHASE 2] {self} can not accept from {upstream}")
            
        return self._can_accept_cache[upstream]