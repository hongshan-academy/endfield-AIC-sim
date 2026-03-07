from typing import List, Optional, Set, Any
from ..item import Item
from .base import BaseComponent


class Conveyor(BaseComponent):
    # Conveyor-specific state
    length: int
    buffer: List[Optional[Item]]
    next_buffer: List[Optional[Item]]
    granted_by_upstream: bool
    granted_to_downstream: bool
    upstream_item: Optional[Item]

    # Lifecycle & Initialization
    def __init__(self, length: int):
        """
        Conveyor initialization.
        
        Args:
            length: Number of slots in the conveyor buffer. Items take
                   'length' ticks to traverse from input to output.
        
        Note:
            Buffer is initialized with None (empty slots).
            Index 0 is input slot, index -1 is output slot.
        """
        self.length = length
        self.buffer = [None] * length
        self.next_buffer = [None] * length
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None

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
        Resets Conveyor to initial state for simulation restart.
        """
        super()._reset()
        self.buffer = [None] * self.length
        self.next_buffer = [None] * self.length
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set[BaseComponent]) -> None:
        """
        Phase 1: Request Propagation (Downstream → Upstream)
        
        Conveyor requests from upstream if it can accept items.
        Conveyor can accept if output slot (buffer[-1]) is empty,
        which means items can shift toward downstream.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Check cycle detection (path_set)
        3. Add self to upstream.pending_requests before calling upstream
        4. Recursively call upstream._phase_1_request()
        5. Do NOT mutate any persistent state
        
        Args:
            tick: Current global tick number
            path_set: Set of components in current recursion path
        """
        # Re-entry guard: prevent double execution in same phase
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        # Cycle detection: prevent infinite recursion in cyclic graphs
        if self in path_set:
            return
        
        new_path = path_set | {self}
        
        # Request from upstream if we can accept items
        # Conveyor can accept if output slot is empty (items can shift)
        if self._can_accept_from_upstream() and self.upstreams:
            for up in self.upstreams:
                if self not in up.pending_requests:
                    up.pending_requests.append(self)
                # Recurse upstream
                up._phase_1_request(tick, new_path)

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Grant Resolution (Upstream → Downstream)
        
        Conveyor grants to downstreams that requested items.
        Conveyor can only grant if output slot (buffer[-1]) has an item.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Process pending_requests from downstreams
        3. Select one downstream (first requester for single output)
        4. Call downstream._receive_grant() for selected downstream
        5. Do NOT fetch items in this phase (happens in P3)
        
        Args:
            tick: Current global tick number
        """
        # Re-entry guard
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        
        # Process requests from downstreams
        if self.pending_requests:
            # Simple arbitration: first requester (Conveyor has single output)
            requester = self.pending_requests[0]
            
            # Can only grant if output slot has an item
            if self.buffer[-1] is not None and requester._can_accept():
                self.granted_to_downstream = True
                # Notify downstream of grant (control signal only)
                requester._receive_grant(self)
        
        # Note: Upstream will call our _receive_grant() if they grant
        # This happens in upstream's _phase_2_grant() method

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: State Preparation
        
        Conveyor calculates next_buffer based on grants:
        1. If granted_to_downstream: items shift toward output
        2. If granted_by_upstream: input slot (buffer[0]) receives item
        3. If both: pass-through (shift + fill input)
        4. If neither: buffer remains unchanged (stall)
        
        Protocol Requirements:
        1. Fetch item from upstream using get_output_item() if granted
        2. Calculate next_buffer based on grants
        3. Do NOT mutate current buffer (happens in P4)
        4. All calculations write to next_buffer only
        
        Note:
            This is the DATA-FETCH phase. Items are fetched but not
            committed until Phase 4.
        """
        # Initialize next_buffer as copy of current buffer
        self.next_buffer = self.buffer.copy()
        
        # Fetch item from upstream if granted (P3 data fetch)
        if self.granted_by_upstream and self.upstreams:
            self.upstream_item = self.upstreams[0].get_output_item()
        
        if self.granted_to_downstream:
            # Items shift toward output (index + 1)
            # Output slot (buffer[-1]) will be transferred out
            for i in range(self.length - 1, 0, -1):
                self.next_buffer[i] = self.buffer[i - 1]
            
            # Input slot: receive from upstream if granted
            if self.granted_by_upstream:
                self.next_buffer[0] = self.upstream_item
            else:
                self.next_buffer[0] = None
        else:
            # No shift (downstream not ready - stall)
            # Buffer remains unchanged
            pass

    def _phase_4_commit(self) -> None:
        """
        Phase 4: Atomic State Commit
        
        Swap next_buffer to buffer. Reset transient state.
        
        Protocol Requirements:
        1. Swap next_buffer to buffer (atomic state change)
        2. Reset all transient state (granted flags, upstream_item, etc.)
        3. Reset visited_tick to -1 (for next tick's re-entry guard)
        4. Clear pending_requests list
        
        Note:
            This is the only phase where buffer is mutated.
            After this phase, all state changes are visible to next tick.
        """
        self.buffer = self.next_buffer
        
        # Reset transient state
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        self.visited_tick = -1
        self.pending_requests = []

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Checks if Conveyor has capacity to accept an item.
        
        Conveyor can accept if output slot (buffer[-1]) is empty.
        This ensures items only move when there's space downstream.
        
        Returns:
            True if output slot is empty, False otherwise.
        
        Note:
            This is used by upstreams during Phase 2 to determine
            if they can grant items to this Conveyor.
        """
        return self.buffer[-1] is None if self.buffer else True

    def _get_capacity(self) -> int:
        """
        Returns the number of available slots in the buffer.
        
        Returns:
            Count of None (empty) slots in buffer.
        """
        return sum(1 for item in self.buffer if item is None)

    def _can_accept_from_upstream(self) -> bool:
        """
        Determines if Conveyor can accept an item from upstream.
        
        Conveyor can accept from upstream if output slot is empty,
        which means items can shift toward downstream.
        
        Returns:
            True if output slot is empty, False otherwise.
        
        Note:
            Default implementation delegates to _can_accept().
            Conveyor uses the same logic for both methods.
        """
        return self._can_accept()

    # Helper Methods - Grant & Transfer
    def _receive_grant(self, grantor: BaseComponent) -> None:
        """
        Called by upstream component during Phase 2 to signal a grant.
        
        This method notifies the Conveyor that its upstream has approved
        a transfer. The Conveyor will fetch the item in Phase 3.
        
        Args:
            grantor: The upstream component that issued the grant.
        
        Note:
            Sets granted_by_upstream flag for Phase 3 item fetching.
            Does NOT fetch item here (happens in Phase 3).
        """
        self.granted_by_upstream = True

    def get_output_item(self) -> Optional[Item]:
        """
        Returns the item at the output slot (buffer[-1]).
        
        This method is called by downstream components during Phase 3
        to fetch items for their next_state calculation.
        
        Returns:
            The item at output slot, or None if slot is empty.
        
        Note:
            This is READ-ONLY. Does not mutate any state.
        """
        return self.buffer[-1] if self.buffer else None

    # Debug & Inspection Methods
    def _get_state_repr(self) -> str:
        """
        Returns a string representation of Conveyor state for debugging.
        """
        buffer_repr = [item.id if item else 0 for item in self.buffer]
        return f"Conveyor(len={self.length}, buffer={buffer_repr})"

    def get_buffer(self) -> List[Optional[Item]]:
        """
        Returns a copy of the current buffer state.
        
        Note:
            Returns a copy to prevent external mutation.
            For debugging and inspection only.
        """
        return self.buffer.copy()