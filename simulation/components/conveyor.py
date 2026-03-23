from typing import List, Optional
from .component import Component
from ..base import Base
from ..item import Item

import logging

logger = logging.getLogger(__name__)


class Conveyor(Component):
    NEED_ADJUDICATION = False
    
    def __init__(self, capacity: int, name: str = '') -> None:
        super(Conveyor, self).__init__(capacity=capacity, name=name)
    
    def _phase_3_response(self) -> None:
        assert len(self._pending_upstreams) <= 1
        super(Conveyor, self)._phase_3_response()
    
    def _phase_4_send(self) -> None:
        assert len(self._pending_downstreams) <= 1, self._pending_downstreams
        super(Conveyor, self)._phase_4_send()