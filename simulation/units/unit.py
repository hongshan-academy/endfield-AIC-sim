from ..base import Base
from ..item import Item, Inventory

from typing import Set, List, Optional

import logging


logger = logging.getLogger(__name__)


class Unit(Base):
    _inventory: Inventory
    
    _upstream_rr_index:   int
    _downstream_rr_index: int
    
    _selected_upstreams: List[Base]
    
    def __init__(self, capacity: int, name: str = '') -> None:
        super(Unit, self).__init__(name=name)
        
        self._inventory = Inventory(capacity)
        self._upstream_rr_index = 0
        self._downstream_rr_index = 0
        
            
    def _phase_2_adjudicate(self) -> None:
        # | downstream             | current | behaviour |
        # | ---------------------- | ------- | --------- |
        # | c + _can_accept() >= n | c < n   | accept    |
        # | c + _can_accept() < n  | c < n   | reject    |

        assert not self._has_received_item

        current_remaining = sum(self._inventory.remaining_capacity().values())

        downstream_accept_sum = sum(
            int(downstream._can_accept(self, set(), phase=2))
            for downstream in self._downstreams
        )
            
        num_upstreams = len(self._upstreams)
        for _ in range(num_upstreams):
            self._upstream_rr_index = (self._upstream_rr_index + 1) % num_upstreams
            upstream = self._upstreams[self._upstream_rr_index]

            if upstream not in self._pending_upstreams:
                continue

            if current_remaining + downstream_accept_sum < 1:
                break
            
            logger.debug(f"[PHASE 2] \"{self}\" --(select)-> \"{upstream}\" (index={self._upstream_rr_index})")
            self._selected_upstreams.append(upstream)
            current_remaining -= 1
            
    def _phase_3_response(self) -> None:
        assert not self._has_received_item

        for upstream in self._selected_upstreams:
            self._grant(upstream)

    def _phase_4_send(self) -> None:        
        for _ in range(len(self._downstreams)):
            self._downstream_rr_index = (self._downstream_rr_index + 1) % len(self._downstreams)
            downstream = self._downstreams[self._downstream_rr_index]
            if not self._inventory.has_item():
                return
            if downstream in self._pending_downstreams:
                self._send_item(phase=4, downstream=downstream)
    
    def _phase_5_commit(self) -> None:
        for i in range(len(self._input)):
            item = self._input[i]
            if item is None:
                continue
            
            if self._inventory.can_push(item.type):
                self._inventory.push(item)
                self._input[i] = None

        assert all(i is None for i in self._input)
    
    def _send_item(self, phase: int = 4, downstream: Optional[Base] = None) -> None:
        if downstream is None:
            return
        
        item = self._inventory.pop()
        logger.debug(f"[PHASE {phase}] \"{self}\" --(\"{item}\")-> \"{self._downstreams[self._downstream_rr_index]}\" (index={self._downstream_rr_index})")
                
        assert item is not None
                
        downstream._receive_item(self, item)
        self._has_sent_item = True

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
        
        if upstream != self._upstreams[self._upstream_rr_index]:
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
    
    def _want_to_send(self) -> bool:
        return self._inventory.has_item()
    
    def _reset(self) -> None:
        super(Unit, self)._reset()
        self._selected_upstreams = []
    
    def _has_empty_slot(self) -> bool:
        return sum(self._inventory.remaining_capacity().values()) > 0
