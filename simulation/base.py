from typing import Optional, List, Dict, Set
import logging

from .item import Item

logger = logging.getLogger(__name__)


class Base(object):
    # const
    NEED_ADJUDICATION: bool
    
    # states
    _input: List[Optional[Item]]
    
    # connections
    _upstreams:   List['Base']
    _downstreams: List['Base']
    
    # transient flags/variables
    _pending_upstreams:   List['Base']
    _pending_downstreams: List['Base']
    _can_accept_cache: Dict['Base', bool]
    _phase_1_visited: Set['Base']
    
    # 剪枝
    _has_received_item: bool
    _has_sent_item:     bool
    
    # for debug
    name: str
    
    def __init__(self, name: str = '') -> None:        
        self._input       = []
        self._upstreams   = []
        self._downstreams = []
        
        self._pending_upstreams   = []
        self._pending_downstreams = []
        
        self.name = name
    
        self._reset()
        
    def connect_to(self, downstream: 'Base') -> None:
        if downstream not in self._downstreams:
            self._downstreams.append(downstream)
            downstream._upstreams.append(self)
            downstream._input.append(None)
    
    # phases interfaces
    def phase_1_tick(self) -> None:
        self._phase_1_request()
    
    def phase_2_tick(self) -> None:
        if self._has_received_item:
            return
        
        self._phase_2_adjudicate()
    
    def phase_3_tick(self) -> None:
        if self._has_received_item:
            return
        
        if not self._pending_upstreams:
            logger.debug(f"[PHASE 3] \"{self}\" has no pending upstreams")
            return
        
        self._phase_3_response()
    
    def phase_4_tick(self) -> None:
        if self._has_sent_item:
            return
        
        if not self._pending_downstreams:
            logger.debug(f"[PHASE 4] \"{self}\" has no pending downstreams")
            return
        
        self._phase_4_send()
    
    def phase_5_tick(self) -> None:
        self._phase_5_commit()
    
        self._reset()
        
    # phases method
    def _phase_1_request(
        self, 
        upstream: Optional['Base'] = None, 
        path: Optional[Set['Base']] = None
    ) -> None:
        """_phase 1_
        
        向下游发送递送请求. 
        
        Args:
            upstream (Optional[&#39;Base&#39;], optional): 上游请求发送方. Defaults to None.
            path (Optional[Set[&#39;Base&#39;]], optional): 递归路径. Defaults to None.
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
        pass
    
    def _phase_3_response(self) -> None:
        """_phase 3_
        
        拒绝/接受上游的请求. 
        """        
        for upstream in self._pending_upstreams:
            if self._can_accept(upstream, set()):
                logger.debug(f"[PHASE 3] \"{self}\" --(grants)-> \"{upstream}\"")
                self._grant(upstream)
    
    def _phase_4_send(self) -> None:
        """_phase 4_
        
        根据先前的请求-裁决-批准的结果向下游传递物品. 
        """        
        # for conveyor/converger:
        #    downstream grants `push` -> push
        # for splitter:
        #    make selection based on the Round-Robin index
        
        self._send_item(phase=4)
    
    def _phase_5_commit(self) -> None:
        """_phase 5_
        
        更新自己的状态. 重置中间变量. 
        """
        raise NotImplementedError
    
    # helper methods
    def _want_to_send(self) -> bool:
        """判断是否有需要递送的物品. 

        Returns:
            bool: 有需要递送的物品时返回 `True`. 
        """
        raise NotImplementedError
    
    def _has_empty_slot(self) -> bool:
        """判断是否有空位

        Returns:
            bool: 有空位则返回 `True`. 
        """
        raise NotImplementedError

    def _grant(self, upstream: "Base") -> None:
        upstream._pending_downstreams.append(self)
    
    def _can_accept(self, upstream: 'Base', path: Set['Base'], phase=3) -> bool:
        """是否能接受来自上游的物品. 

        | downstream     | [current]      | behaviour |
        | -------------- | -------------- | --------- |
        | ~              | has-empty-slot | grant     |
        | has-empty-slot | full           | grant     |
        | full           | full           | recursion |
        
        Args:
            upstream (Base): 上游请求发送方. 
            path (Set[&#39;Base&#39;]): 递归路径
            phase (int, optional): 调用时所处的阶段，用于日志. Defaults to 3.

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
        """
        raise NotImplementedError

    def _receive_item(self, upstream: 'Base', item: Item) -> None:
        """从上游接受物品. 

        Args:
            item (Item): 来自上游的物品
        """
        
        upstream_idx = self._upstreams.index(upstream)
        assert upstream_idx >= 0
        self._input[upstream_idx] = item
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