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
            logger.debug(f"[PHASE 2] {self} has no pending upstreams")
            return
        
        if not self._can_accept(set()):
            logger.debug(f"[PHASE 2] {self} cannot accept")
            return
        
        for _ in range(len(self._upstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._upstreams)
            upstream = self._upstreams[self._rr_index]
            if upstream in self._pending_upstreams:
                logger.debug(f"[PHASE 2] {self} grants {upstream} (index={self._rr_index})")
                self._grant(upstream)
                break

    def _phase_3_send(self) -> None:        
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        
        if self._pending_downstreams:
            logger.debug(f"[PHASE 3] {self} sends {self._items[0]} to {self._pending_downstreams[0]}")
            self._pending_downstreams[0]._input, self._items[0] = self._items[0], None
