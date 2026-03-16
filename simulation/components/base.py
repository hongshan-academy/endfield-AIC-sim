from typing import Optional, List, Dict, Set
import logging

from ..item import Item
from . import *

logger = logging.getLogger(__name__)


class Component(object):
    # const
    NEED_ADJUDICATION: bool
    
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
    
    # 剪枝
    _has_received_item: bool
    _has_sent_item:     bool
    
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
        """_phase 1_
        
        向下游发送递送请求. 
        
        Args:
            upstream (Optional[&#39;Component&#39;], optional): _description_. Defaults to None.
            path (Optional[Set[&#39;Component&#39;]], optional): _description_. Defaults to None.
        """
        
        # TODO: 剪枝
        # 1. 普通器件下游（非汇流/units）空 -> 直接递送
        # 2. 分流器 _rr_index + i 下游（非汇流/units）空 -> 直接递送
        
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
        
        for downstream in self._downstreams:
            if not self._want_to_send():
                break
            
            if not downstream.NEED_ADJUDICATION and downstream._has_empty_slot():
                self._pending_downstreams.append(downstream)
                self._send_item(phase=1)
                continue
            
            downstream._phase_1_request(self, path)
        
        path.remove(self)
    
    def _phase_2_adjudicate(self) -> None:
        """_phase 2_
        
        可能出现满/阻塞的、需要对下游进行选择的器件需要实现这个方法. 该方法用于对下游请求进行裁决/选择. 
        """
        if self._has_received_item:
            return
    
    def _phase_3_response(self) -> None:
        """_phase 3_
        
        拒绝/接受上游的请求. 
        """
        if self._has_received_item:
            return
        
        if not self._pending_upstreams:
            logger.debug(f"[PHASE 3] \"{self}\" has no pending upstreams")
            return
        
        for upstream in self._pending_upstreams:
            if self._can_accept(upstream, set()):
                logger.debug(f"[PHASE 3] \"{self}\" --(grants)-> \"{upstream}\"")
                self._grant(upstream)
    
    def _phase_4_send(self) -> None:
        """_phase 4_
        
        根据先前的请求-裁决-批准的结果向下游传递物品. 
        """
        if self._has_sent_item:
            return
        
        # for conveyor/converger:
        #    downstream grants `push` -> push
        # for splitter:
        #    make selection based on the Round-Robin index
        
        if self._pending_downstreams:
            self._send_item(phase=4)
    
    def _phase_5_commit(self) -> None:
        """_phase 5_
        
        更新自己的状态. 重置中间变量. 
        """    
        for i in range(len(self._items) - 1):
            if self._items[i] is None and self._items[i + 1] is not None:
                self._items[i], self._items[i + 1] = self._items[i + 1], self._items[i]
        
        if self._items[-1] is None:
            self._items[-1], self._input = self._input, None
        
        self._reset()
    
    # component-specific methods
    def _want_to_send(self) -> bool:
        """判断是否有需要递送的物品. 

        Returns:
            bool: 有需要递送的物品时返回 `True`. 
        """
        return self._items[0] is not None
    
    # helper methods
    def _has_empty_slot(self) -> bool:
        """判断是否有空位

        Returns:
            bool: 有空位则返回 `True`. 
        """
        return None in self._items

    def _grant(self, upstream: "Component") -> None:
        upstream._pending_downstreams.append(self)
    
    def _can_accept(self, upstream: 'Component', path: Set['Component'], phase=3) -> bool:
        """是否能接受来自上游的物品. 

        | downstream     | [current]      | behaviour |
        | -------------- | -------------- | --------- |
        | ~              | has-empty-slot | grant     |
        | has-empty-slot | full           | grant     |
        | full           | full           | recursion |
        
        Args:
            upstream (Component): _description_
            path (Set[&#39;Component&#39;]): _description_
            phase (int, optional): _description_. Defaults to 3.

        Returns:
            bool: 是否可以接受. 
        """
        
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
    
    def _send_item(self, phase: int = 4) -> None:
        """向下游递送物品. 

        Raises:
            NotImplementedError: 每个器件必须实现这个方法. 
        """
        
        item, self._items[0] = self._items[0], None
        assert item is not None
        self._pending_downstreams[0]._receive_item(item)
        logger.debug(f"[PHASE {phase}] \"{self}\" --(\"{item}\")-> \"{self._pending_downstreams[0]}\"")
        self._has_sent_item = True

    def _receive_item(self, item: Item) -> None:
        """从上游接受物品. 

        Args:
            item (Item): 来自上游的物品
        """
        
        self._input = item
        self._has_received_item = True
    
    def _reset(self) -> None:
        """重置中间变量. 
        """
        self._pending_upstreams   = []
        self._pending_downstreams = []
        self._can_accept_cache = {}
        self._phase_1_visited = set()
        
        self._has_received_item = False
        self._has_sent_item =     False
        
    def __repr__(self) -> str:
        return str(self)
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.__class__.__name__}.{self.name}"
        else:
            return f"{self.__class__.__name__}"