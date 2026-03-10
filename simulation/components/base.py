from typing import Optional, List, Dict, Set
import logging

from ..item import Item

logger = logging.getLogger(__name__)


class Component(object):
    # states
    _items: List[Optional[Item]]
    _input: Optional[Item]
    
    # connections
    _upstreams:   List['Component']
    _downstreams: List['Component']
    
    # transient flags/variables
    _pending_upstreams:   List['Component']
    _pending_downstreams: List['Component']
    _can_accept_cache: Dict['Component', bool]
    _phase_1_visited: Set['Component']
    
    # for debug
    name: str
    
    def __init__(self, capacity: int, name: str = '') -> None:
        self._visited = [False, False]
        
        self._items = [None] * capacity
        self._input = None
        
        self._upstreams   = []
        self._downstreams = []
        
        self._pending_upstreams   = []
        self._pending_downstreams = []
        
        self.name = name
        
        self._reset()
    
    def connect_to(self, downstream: 'Component') -> None:
        if downstream not in self._downstreams:
            self._downstreams.append(downstream)
            downstream._upstreams.append(self)
    
    # phases method
    def _phase_1_request(
        self, 
        upstream: Optional['Component'] = None, 
        path: Optional[Set['Component']] = None
    ) -> None:
        if upstream is not None and upstream in self._phase_1_visited:
            return
        
        if path is None:
            path = set()
        
        if self in path:
            return
        
        if upstream is not None:
            logger.debug(f"[PHASE 1] {upstream} requests {self}")
            self._pending_upstreams.append(upstream)
            self._phase_1_visited.add(upstream)
            
        path.add(self)
        
        if self._want_to_send():
            for downstream in self._downstreams:
                downstream._phase_1_request(self, path)
        
        path.remove(self)
    
    def _phase_2_response(self) -> None:
        if not self._pending_upstreams:
            logger.debug(f"[PHASE 2] {self} has no pending upstreams")
            return
        
        for upstream in self._pending_upstreams:
            if self._can_accept(upstream, set()):
                logger.debug(f"[PHASE 2] {self} grants {upstream}")
                self._grant(upstream)
    
    def _phase_3_send(self) -> None:
        # for conveyor/converger:
        #    downstream grants `push` -> push
        # for splitter:
        #    make selection based on the Round-Robin index
        
        raise NotImplementedError
    
    def _phase_4_commit(self) -> None:
        # update & reset
    
        for i in range(len(self._items) - 1):
            if self._items[i] is None and self._items[i + 1] is not None:
                self._items[i], self._items[i + 1] = self._items[i + 1], self._items[i]
        
        if self._items[-1] is None:
            logger.debug(f"[PHASE 4] {self} accepts {self._input}")
            self._items[-1], self._input = self._input, None      
                
        self._reset()
    
    # component-specific methods
    def _want_to_send(self) -> bool:
        return self._items[0] is not None
    
    # helper methods
    def _has_empty_slot(self) -> bool:
        return None in self._items

    def _grant(self, upstream: "Component") -> None:
        upstream._pending_downstreams.append(self)
    
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
    
    def _reset(self) -> None:
        self._pending_upstreams   = []
        self._pending_downstreams = []
        self._can_accept_cache = {}
        self._phase_1_visited = set()
        
    def __repr__(self) -> str:
        return str(self)
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.__class__.__name__}.{self.name}({self._items})"
        else:
            return f"{self.__class__.__name__}({self._items})"