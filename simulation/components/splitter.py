from typing import Set, Optional

from .base import Component

import logging

logger = logging.getLogger(__name__)

class Splitter(Component):
    NEED_ADJUDICATION = False
    
    _rr_index: int
    
    def __init__(self, name: str = '') -> None:
        super(Splitter, self).__init__(capacity=1, name=name)
        
        self._rr_index = 0
    
    def _phase_1_request(
        self, 
        upstream: Optional['Component'] = None, 
        path: Optional[Set['Component']] = None
    ) -> None:
        """_phase 1_
        
        向下游发送递送请求. 
        
        Args:
            upstream (Optional[&#39;Component&#39;], optional): _description_. Defaults to None.
            path (Optional[Set[&#39;Component&#39;]], optional): _description_. Defaults to None.
        """
        if upstream is not None and upstream in self._phase_1_visited:
            return
        
        if path is None:
            path = set()
        
        if self in path:
            return
        
        if upstream is not None:
            logger.debug(f"[PHASE 1] \"{upstream}\" --(requests)-> \"{self}\"")
            self._pending_upstreams.append(upstream)
            self._phase_1_visited.add(upstream)
            
        path.add(self)
        
        for _ in range(len(self._downstreams)):    
            if not self._want_to_send():
                break
            
            self._rr_index = (self._rr_index + 1) % len(self._downstreams)
            downstream = self._downstreams[self._rr_index]
            
            if not downstream.NEED_ADJUDICATION and downstream._has_empty_slot():
                logger.debug(f'[PHASE 1] \"{self}\" --(pre-send)-> \"{downstream}\"')
                self._send_item(phase=1, downstream=downstream)
                continue
                
            downstream._phase_1_request(self, path)
        
        path.remove(self)
    
    def _phase_3_response(self) -> None:
        assert len(self._pending_upstreams) <= 1
        
        super(Splitter, self)._phase_3_response()
    
    def _phase_4_send(self) -> None:        
        for _ in range(len(self._downstreams)):
            self._rr_index = (self._rr_index + 1) % len(self._downstreams)
            downstream = self._downstreams[self._rr_index]
            if downstream in self._pending_downstreams:
                self._send_item(phase=4, downstream=downstream)
                return
    
    def _send_item(self, phase: int = 4, downstream: Optional[Component] = None) -> None:
        if downstream is None:
            return
                
        item, self._items[0] = self._items[0], None
        logger.debug(f"[PHASE {phase}] \"{self}\" --(\"{item}\")-> \"{self._downstreams[self._rr_index]}\" (index={self._rr_index})")
                
        assert item is not None
                
        downstream._receive_item(item)
        self._has_sent_item = True

