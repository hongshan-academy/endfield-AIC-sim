from .base import Component

import logging

logger = logging.getLogger(__name__)


class Conveyor(Component):
    def __init__(self, capacity: int, name: str = '') -> None:
        super(Conveyor, self).__init__(capacity, name)
    
    def _phase_2_response(self) -> None:
        assert len(self._pending_upstreams) <= 1
        
        super(Conveyor, self)._phase_2_response()
    
    def _phase_3_send(self) -> None:        
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        
        if self._pending_downstreams:
            logger.debug(f"[PHASE 4] {self} sends {self._items[0]} to {self._pending_downstreams[0]}")
            self._pending_downstreams[0]._input, self._items[0] = self._items[0], None
