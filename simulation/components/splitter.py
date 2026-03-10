from .base import Component

import logging

logger = logging.getLogger(__name__)

class Splitter(Component):
    _rr_index: int
    
    def __init__(self, name: str = '') -> None:
        super(Splitter, self).__init__(capacity=1, name=name)
        
        self._rr_index = 0
    
    def _phase_2_response(self) -> None:
        assert len(self._pending_upstreams) <= 1
        
        super(Splitter, self)._phase_2_response()
    
    def _phase_3_send(self) -> None:
        if not self._pending_downstreams:
            return
        
        for _ in range(len(self._downstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._downstreams)
            downstream = self._downstreams[self._rr_index]
            if downstream in self._pending_downstreams:
                logger.debug(f"[PHASE 3] {self} sends {self._items[0]} to {self._downstreams[self._rr_index]} (index={self._rr_index})")
                downstream._input, self._items[0] = self._items[0], None
                break
