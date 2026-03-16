from typing import Optional, List, Dict, Set
import logging

from ..item import Item

logger = logging.getLogger(__name__)

class Unit(object):
    # states
    _items: List[Optional[Item]]
    _input: Optional[Item]
    
    # connections
    _upstreams:   List['Unit']
    _downstreams: List['Unit']
    
    # transient flags/variables
    _pending_upstreams:   List['Unit']
    _pending_downstreams: List['Unit']
    _can_accept_cache: Dict['Unit', bool]
    _phase_1_visited: Set['Unit']
    
    # for debug
    name: str
    
    def __init__(self, capacity: int, name: str = '') -> None:        
        self._items = [None] * capacity
        self._input = None
        
        self._upstreams   = []
        self._downstreams = []
        
        self._pending_upstreams   = []
        self._pending_downstreams = []
        
        self.name = name
        
        self._reset()
    
    def connect_to(self, downstream: 'Unit') -> None:
        if downstream not in self._downstreams:
            self._downstreams.append(downstream)
            downstream._upstreams.append(self)
    
    # phases method
    def _phase_1_request(
        self, 
        upstream: Optional['Unit'] = None, 
        path: Optional[Set['Unit']] = None
    ) -> None:
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
        
        if self._want_to_send():
            for downstream in self._downstreams:
                downstream._phase_1_request(self, path)
        
        path.remove(self)
    
    def _phase_2_adjudicate(self) -> None:
        pass
    
    def _phase_3_response(self) -> None:
        if not self._pending_upstreams:
            logger.debug(f"[PHASE 3] \"{self}\" has no pending upstreams")
            return
        
        for upstream in self._pending_upstreams:
            if self._can_accept(upstream, set()):
                logger.debug(f"[PHASE 3] \"{self}\" --(grants)-> \"{upstream}\"")
                self._grant(upstream)
    
    def _phase_4_send(self) -> None:
        # for conveyor/converger:
        #    downstream grants `push` -> push
        # for splitter:
        #    make selection based on the Round-Robin index
        
        raise NotImplementedError
    
    def _phase_5_commit(self) -> None:
        # update & reset
    
        for i in range(len(self._items) - 1):
            if self._items[i] is None and self._items[i + 1] is not None:
                self._items[i], self._items[i + 1] = self._items[i + 1], self._items[i]
        
        if self._items[-1] is None:
            self._items[-1], self._input = self._input, None      
    
    # Unit-specific methods
    def _want_to_send(self) -> bool:
        return self._items[0] is not None
    
    # helper methods
    def _has_empty_slot(self) -> bool:
        return None in self._items

    def _grant(self, upstream: "Unit") -> None:
        upstream._pending_downstreams.append(self)
    
    def _can_accept(self, upstream: 'Unit', path: Set['Unit']) -> bool:
        # | downstream     | [current]      | behaviour |
        # | -------------- | -------------- | --------- |
        # | ~              | has-empty-slot | grant     |
        # | has-empty-slot | full           | grant     |
        # | full           | full           | recursion |
        
        # cycle detection
        if self in path:
            logger.debug(f"[PHASE 3] \"{self}\" detects cycle in path {path}")
            # this should not be cached
            return False
        
        if self._can_accept_cache.get(upstream) is not None:
            if self._can_accept_cache[upstream]:
                logger.debug(f"[PHASE 3] \"{self}\" --(can accept)-> \"{upstream}\" (cached)")
            else:
                logger.debug(f"[PHASE 3] \"{self}\" --(cannot accept)-> \"{upstream}\" (cached)")
                
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
            logger.debug(f"[PHASE 3] \"{self}\" --(can accept)-> \"{upstream}\"")
        else:
            logger.debug(f"[PHASE 3] \"{self}\" --(cannot accept)-> \"{upstream}\"")
            
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
            return f"{self.__class__.__name__}.{self.name}"
        else:
            return f"{self.__class__.__name__}"