from typing import List, Optional, Set, Any
from ..item import Item
from .base import BaseComponent


class Source(BaseComponent):
    # Source-specific state
    item_list: List[Item]
    current_index: int
    granted_downstream: Optional[BaseComponent]
    next_state_item: Optional[Item]

    # Lifecycle & Initialization
    def __init__(self, item_list: List[Item]):
        """
        Source initialization.
        
        Args:
            item_list: List of items to cycle through. Source will emit
                      these items in order, repeating when exhausted.
        
        Note:
            item_list must not be empty. Items are never discarded by Source;
            if downstream is blocked, the index pauses until space is available.
        """
        self.item_list = item_list
        self.current_index = 0
        self.granted_downstream = None
        self.next_state_item = None

    def set_context(self, context: Any) -> None:
        """
        Injects the global simulation context.
        
        Args:
            context: Reference to the global simulation controller.
        """
        super().set_context(context)
        self.visited_tick = -1
        self.pending_requests = []
        # self.downstreams = []

    def _reset(self) -> None:
        """
        Resets Source to initial state for simulation restart.
        """
        super(Source, self)._reset()
        self.current_index = 0
        self.granted_downstream = None
        self.next_state_item = None

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set[BaseComponent]) -> None:
        """
        Phase 1: Request Propagation (Downstream → Upstream)
        
        Source is the end of the pull chain. It does not have upstreams,
        so it only records that downstreams have requested items.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Check cycle detection (path_set)
        3. Do NOT recurse upstream (Source has no upstreams)
        4. Downstreams have already added themselves to pending_requests
        
        Args:
            tick: Current global tick number
            path_set: Set of components in current recursion path
        """
        # Re-entry guard: prevent double execution in same phase
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        # Cycle detection: Source should not be in a cycle
        if self in path_set:
            return
        
        # Source has no upstreams to request from
        # Downstreams have already added themselves to pending_requests
        # before calling this method
        pass

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Grant Resolution (Upstream → Downstream)
        
        Source selects one downstream from pending_requests and grants
        permission to receive an item.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Process pending_requests from downstreams
        3. Select one downstream (arbitration)
        4. Call downstream._receive_grant() for selected downstream
        5. Do NOT fetch or prepare items in this phase
        
        Args:
            tick: Current global tick number
        """
        # Re-entry guard
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        self.granted_downstream = None
        
        # Select downstream from pending_requests
        if self.pending_requests:
            # Simple arbitration: first requester
            # Can be extended to round-robin or priority-based
            requester = self.pending_requests[0]
            
            if requester._can_accept():
                self.granted_downstream = requester
                # Notify downstream of grant (control signal only)
                requester._receive_grant(self)

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: State Preparation
        
        Source prepares the item to be emitted if a downstream was granted.
        
        Protocol Requirements:
        1. Fetch item from item_list based on current_index
        2. Store in next_state_item (not committed yet)
        3. Do NOT mutate current_index yet (happens in P4)
        
        Note:
            This is the DATA-FETCH phase. The item is prepared but not
            committed until Phase 4.
        """
        self.next_state_item = None
        
        if self.granted_downstream is not None:
            # Prepare the item for transfer
            self.next_state_item = self.item_list[self.current_index]

    def _phase_4_commit(self) -> None:
        """
        Phase 4: Atomic State Commit
        
        If transfer was granted, increment index. Reset transient state.
        
        Protocol Requirements:
        1. If granted, increment current_index (cycle through item_list)
        2. Reset all transient state (granted flags, next_state_item, etc.)
        3. Reset visited_tick to -1
        4. Clear pending_requests list
        
        Note:
            This is the only phase where current_index is mutated.
        """
        if self.granted_downstream is not None:
            # Only increment if item was actually transferred
            self.current_index = (self.current_index + 1) % len(self.item_list)
        
        # Reset transient state
        self.granted_downstream = None
        self.next_state_item = None
        self.visited_tick = -1
        self.pending_requests = []

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Source never accepts items (it is a producer, not a consumer).
        
        Returns:
            Always False.
        """
        return False

    def _get_capacity(self) -> int:
        """
        Source has no input capacity.
        
        Returns:
            Always 0.
        """
        return 0

    def _can_accept_from_upstream(self) -> bool:
        """
        Source cannot accept from upstream (no upstream exists).
        
        Returns:
            Always False.
        """
        return False

    # Helper Methods - Grant & Transfer
    def _receive_grant(self, grantor: BaseComponent) -> None:
        """
        Source never receives grants (it has no upstream).
        
        Args:
            grantor: Ignored (Source has no upstream).
        """
        pass

    def get_output_item(self) -> Optional[Item]:
        """
        Returns the item ready to be transferred to downstream.
        
        This method is called by downstream components during Phase 3
        to fetch the item for their next_state calculation.
        
        Returns:
            The prepared item (next_state_item), or None if no grant.
        
        Note:
            This is READ-ONLY. Does not mutate any state.
        """
        return self.next_state_item

    # Debug & Inspection Methods
    def _get_state_repr(self) -> str:
        """
        Returns a string representation of Source state for debugging.
        
        Returns:
            Human-readable string with current_index and next item.
        """
        next_item = self.item_list[self.current_index] if self.item_list else None
        return f"Source(idx={self.current_index}, next={next_item})"