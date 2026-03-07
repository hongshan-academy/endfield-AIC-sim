from typing import Set, List, Optional, TYPE_CHECKING
from ..item import Item

if TYPE_CHECKING:
    from .base import BaseComponent


class BaseComponent(object):
    def __init__(self) -> None:
        self.upstream_components: List["BaseComponent"] = []
        self.downstream_components: List["BaseComponent"] = []
        self.buffer: Optional[Item] = None
        self.next_buffer: Optional[Item] = None
        self.visited: bool = False
        self.acknowledged_by_downstream: bool = False
        self.path: Set["BaseComponent"] = set()

    def connect(self, upstreams: List["BaseComponent"]) -> None:
        for upstream in upstreams:
            upstream.downstream_components.append(self)
            self.upstream_components.append(upstream)

    def _can_push_to_downstream(self) -> bool:
        raise NotImplementedError

    def _phase_1_request(self, path: Set["BaseComponent"]) -> bool:
        # 1. cycle detection
        if self in path:
            return False
        # 2. check if self.want-to-push
        self.path = path.copy()
        self.path.add(self)
        if self._can_push_to_downstream():
            for ds in self.downstream_components:
                if not ds._phase_1_request(self.path):
                    return False
            return True
        return False

    def _phase_2_response(self) -> bool:
        # 1. visited check
        if self.visited:
            return True
        self.visited = True
        # 2. has-item + downstream-ready -> send_response_ack
        result = True
        for ds in self.downstream_components:
            if not ds._phase_2_response():
                result = False
        if self.buffer is not None and self._downstream_ready():
            self.acknowledged_by_downstream = True
        return result

    def _downstream_ready(self) -> bool:
        for ds in self.downstream_components:
            if ds.buffer is None:
                return True
        return len(self.downstream_components) == 0

    def _phase_3_compute(self) -> None:
        # Calculate next_state
        self.next_buffer = None
        if self.acknowledged_by_downstream and self.buffer is not None:
            self._push_output_item()

    def _push_output_item(self) -> None:
        for ds in self.downstream_components:
            if ds.buffer is None:
                ds.next_buffer = self.buffer
                self.next_buffer = None
                break

    def _phase_4_update(self) -> None:
        # buffer = next_buffer, reset transient state
        self.buffer = self.next_buffer
        self.visited = False
        self.acknowledged_by_downstream = False
        self.path = set()

    def _send_approve(self) -> None:
        pass

    def get_buffer(self) -> List[Optional[Item]]:
        return [self.buffer]

    def has_item(self) -> bool:
        return self.buffer is not None