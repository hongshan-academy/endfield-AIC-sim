from typing import List, Optional, Set, Any
from ..item import Item
from .base import BaseComponent


class Sink(BaseComponent):
    # Sink-specific state
    items_received: int
    received_items: List[Item]
    granted_by_upstream: bool
    next_state_item: Optional[Item]

    # Lifecycle & Initialization
    def __init__(self):
        """
        Sink initialization.
        
        Note:
            Sink has infinite capacity and never blocks the pipeline.
            Items are discarded after being received (removed from simulation).
            received_items list is for debugging/tracking only.
        """
        self.items_received = 0
        self.received_items = []
        self.granted_by_upstream = False
        self.next_state_item = None

    def set_context(self, context: Any) -> None:
        """
        Injects the global simulation context.
        """
        super().set_context(context)
        self.visited_tick = -1
        self.pending_requests = []
        # self.downstreams = []

    def _reset(self) -> None:
        """
        Resets Sink to initial state for simulation restart.
        """
        super()._reset()
        self.items_received = 0
        self.received_items = []
        self.granted_by_upstream = False
        self.next_state_item = None

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set[BaseComponent]) -> None:
        """
        Phase 1: Request Propagation (Downstream → Upstream)
        
        Sink initiates the pull chain by requesting from all upstreams.
        Sink always has capacity, so it always requests.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Check cycle detection (path_set)
        3. Add self to all upstreams' pending_requests
        4. Recursively call upstream._phase_1_request()
        """
        # Re-entry guard
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        # Cycle detection
        if self in path_set:
            return
        
        new_path = path_set | {self}
        
        # Request from all upstreams (Sink always has capacity)
        for up in self.upstreams:
            if self not in up.pending_requests:
                up.pending_requests.append(self)
            # Recurse upstream
            up._phase_1_request(tick, new_path)

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Grant Resolution (Upstream → Downstream)
        
        Sink receives grants from upstreams. Sink has no downstreams,
        so it does not issue any grants.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Do NOT issue grants (Sink has no downstreams)
        3. Upstreams will call _receive_grant() if they grant
        """
        # Re-entry guard
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        # Sink does not grant to downstreams (none exist)
        # Upstreams handle grant logic on their side
        pass

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: State Preparation
        
        Sink fetches item from upstream if granted.
        
        Protocol Requirements:
        1. If granted_by_upstream, fetch item from upstream
        2. Store in next_state_item (not committed yet)
        3. Do NOT mutate items_received yet (happens in P4)
        
        Note:
            This is the DATA-FETCH phase. Item is fetched but not
            committed until Phase 4.
        """
        self.next_state_item = None
        
        if self.granted_by_upstream and self.upstreams:
            # Fetch item from first upstream
            # (For multiple upstreams, may need merge logic)
            self.next_state_item = self.upstreams[0].get_output_item()

    def _phase_4_commit(self) -> None:
        """
        Phase 4: Atomic State Commit
        
        Accept item (discard from simulation). Reset transient state.
        
        Protocol Requirements:
        1. If item received, increment items_received counter
        2. Optionally store item in received_items (for tracking)
        3. Reset all transient state (granted flags, next_state_item, etc.)
        4. Reset visited_tick to -1
        5. Clear pending_requests list
        
        Note:
            Items are discarded here (removed from simulation).
            received_items is optional for debugging.
        """
        if self.next_state_item is not None:
            self.items_received += 1
            self.received_items.append(self.next_state_item)
            # Item is discarded (not stored in buffer)
        
        # Reset transient state
        self.granted_by_upstream = False
        self.next_state_item = None
        self.visited_tick = -1
        self.pending_requests = []

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Sink always accepts items (infinite capacity).
        """
        return True

    def _get_capacity(self) -> int:
        """
        Sink has infinite capacity.
        """
        return 999999

    def _can_accept_from_upstream(self) -> bool:
        """
        Sink always accepts from upstream (infinite capacity).
        """
        return True

    # Helper Methods - Grant & Transfer
    def _receive_grant(self, grantor: BaseComponent) -> None:
        """
        Called by upstream to signal grant.
        """
        self.granted_by_upstream = True

    def get_output_item(self) -> Optional[Item]:
        """
        Sink has no output (it is the end of the pipeline).
        """
        return None

    # Debug & Inspection Methods
    def _get_state_repr(self) -> str:
        """
        Returns a string representation of Sink state for debugging.
        """
        return f"Sink(received={self.items_received})"

    def record_item(self, item: Item) -> None:
        """
        Records an item that was received (for debugging/tracking).
        """
        self.items_received += 1
        self.received_items.append(item)