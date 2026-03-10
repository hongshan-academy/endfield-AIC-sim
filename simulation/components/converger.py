from typing import Set, Optional
from .base import Component
import logging

logger = logging.getLogger(__name__)


class Converger(Component):
    _rr_index: int
    
    def __init__(self, name: str = '') -> None:
        super(Converger, self).__init__(capacity=1, name=name)
        
        self._rr_index = 0
    
    def _phase_2_adjudicate(self) -> None:
        if not self._pending_upstreams:
            return
        
        for _ in range(len(self._upstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._upstreams)
            upstream = self._upstreams[self._rr_index]
            if upstream in self._pending_upstreams:
                logger.debug(f"[PHASE 2] {self} selects {upstream} (index={self._rr_index})")
                break
    
    def _phase_3_response(self) -> None:
        if not self._can_accept(set(), self):
            return
        
        if self._upstreams[self._rr_index] in self._pending_upstreams:
            upstream = self._upstreams[self._rr_index]
            logger.debug(f"[PHASE 3] {self} grants {upstream} (index={self._rr_index})")
            self._grant(upstream)

    def _phase_4_send(self) -> None:        
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        
        if self._pending_downstreams:
            logger.debug(f"[PHASE 4] {self} sends {self._items[0]} to {self._pending_downstreams[0]}")
            self._pending_downstreams[0]._input, self._items[0] = self._items[0], None

    def _can_accept(self, path: Set[Component], upstream: Optional[Component] = None) -> bool:
        # | downstream     | [current]      | behaviour |
        # | -------------- | -------------- | --------- |
        # | ~              | has-empty-slot | grant     |
        # | has-empty-slot | full           | grant     |
        # | full           | full           | recursion |
        
        # cycle detection
        if self in path:
            logger.debug(f"[PHASE 3] {self} detects cycle in path {path}")
            # this should not be cached
            return False
                
        if self._can_accept_cache is not None:
            logger.debug(f"[PHASE 3] {self} uses cached can_accept value: {self._can_accept_cache}")
            return self._can_accept_cache
        
        path.add(self)
        
        if self._has_empty_slot():
            self._can_accept_cache = True
        elif self._pending_downstreams is None:
            self._can_accept_cache = False
        else:
            self._can_accept_cache = self._upstreams[self._rr_index] == upstream
        
        path.remove(self)
        
        return self._can_accept_cache