from typing import Optional, Set, Any
from ..item import Item
from .base import BaseComponent


class Converger(BaseComponent):
    # Converger-specific state
    buffer: Optional[Item]
    next_buffer: Optional[Item]
    rr_index: int
    granted_by_upstream: bool
    granted_to_downstream: bool
    upstream_item: Optional[Item]
    selected_upstream: Optional[BaseComponent]

    # Lifecycle & Initialization
    def __init__(self, num_inputs: int):
        """
        Converger initialization.
        
        Note:
            Converger has a 1-slot buffer with 1-tick latency.
            Items always enter buffer first, then exit on next tick (no bypass).
            Round-robin ensures fair distribution across upstreams.
            Blocked or empty upstreams are skipped in the rotation.
        """
        self.buffer = None
        self.next_buffer = None
        self.rr_index = 0
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        self.selected_upstream = None
        self._num_inputs = num_inputs

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
        Resets Converger to initial state for simulation restart.
        """
        super()._reset()
        self.buffer = None
        self.next_buffer = None
        self.rr_index = 0
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        self.selected_upstream = None

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set[BaseComponent]) -> None:
        """
        Phase 1: Request Propagation (Downstream → Upstream)
        
        Converger requests from upstream if it can accept items.
        Converger can accept if:
        1. Buffer is empty (can store item), OR
        2. Buffer is full BUT downstream is ready (can pass through)
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Check cycle detection (path_set)
        3. Add self to upstream.pending_requests before calling upstream
        4. Recursively call upstream._phase_1_request()
        5. Do NOT mutate any persistent state
        
        Request Table:
            | downstream | buffer | request? |
            |------------|--------|----------|
            | ready      | empty  | YES      |
            | blocked    | empty  | YES      |
            | ready      | full   | YES      |
            | blocked    | full   | NO       |
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
        # Converger can accept if buffer empty OR downstream ready (pass-through)
        if self._can_accept_from_upstream() and self.upstreams:
            for up in self.upstreams:
                if self not in up.pending_requests:
                    up.pending_requests.append(self)
                # Recurse upstream
                up._phase_1_request(tick, new_path)

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Grant Resolution (Upstream → Downstream)
        
        Converger performs two types of grants:
        1. Grant to downstream: If buffer has item and downstream requested
        2. Select upstream: Round-robin over upstreams with items (skip blocked/empty)
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Process pending_requests from downstreams
        3. Grant to downstream if buffer has item and downstream ready
        4. Select upstream using round-robin (skip blocked/empty upstreams)
        5. Do NOT fetch items in this phase (happens in P3)
        6. Update rr_index for deterministic distribution
        
        Round-Robin Example (3 upstreams, #3 empty):
            Tick 1: rr_index=0 → Select #1 (has item), rr_index→1
            Tick 2: rr_index=1 → Select #2 (has item), rr_index→2
            Tick 3: rr_index=2 → Skip #3 (empty), rr_index→0, Select #1
            Pattern: 1 → 2 → 1 → 2 → ... (skipping #3)
        
        Note:
            This is a CONTROL-ONLY phase. No data transfer allowed.
            Item fetching happens in Phase 3.
        """
        # Re-entry guard
        if self.visited_tick == tick:
            return
        self.visited_tick = tick
        
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        self.selected_upstream = None
        
        # Part 1: Grant to downstream (if we have item and downstream requested)
        if self.buffer is not None and self.pending_requests:
            # Simple: first requester (Converger has single output)
            requester = self.pending_requests[0]
            
            if requester._can_accept():
                self.granted_to_downstream = True
                # Notify downstream of grant (control signal only)
                requester._receive_grant(self)
        
        # Part 2: Select upstream and prepare to receive grant (if can accept)
        if self._can_accept_from_upstream() and self.upstreams:
            # Use modular arbitration logic (skip blocked/empty upstreams)
            self.selected_upstream = self._select_upstream_arbitration()
            
            if self.selected_upstream:
                # Upstream will call our _receive_grant() if they grant
                # This happens in upstream's _phase_2_grant() method
                pass

    def _select_upstream_arbitration(self) -> Optional[BaseComponent]:
        """
        Selects an upstream using round-robin arbitration.
        
        Only considers upstreams that:
        1. Have items available at output (get_output_item() is not None)
        2. Can accept requests (not blocked internally)
        
        Blocked or empty upstreams are SKIPPED in the rotation, but rr_index
        still advances past them to maintain fair distribution.
        
        Example (3 upstreams, #3 empty):
            upstreams = [U1, U2, U3]
            rr_index = 0
            
            Tick 1: Start at 0 → U1 has item? YES → Select U1, rr_index→1
            Tick 2: Start at 1 → U2 has item? YES → Select U2, rr_index→2
            Tick 3: Start at 2 → U3 has item? NO → Skip, rr_index→0
                    Continue at 0 → U1 has item? YES → Select U1, rr_index→1
            Pattern: U1 → U2 → U1 → U2 → ... (U3 skipped)
        
        Note:
            This method is extracted for future modification.
            Alternative arbitration strategies can be implemented here:
            - Priority-based selection
            - Weighted round-robin
            - Least-recently-used
            - Buffer-level aware selection
        """
        if not self.upstreams:
            return None
        
        num_upstreams = len(self.upstreams)
        if num_upstreams == 0:
            return None
        
        # Start from rr_index and search for a valid upstream
        # We may need to wrap around multiple times if many are blocked/empty
        for i in range(num_upstreams):
            idx = (self.rr_index + i) % num_upstreams
            candidate = self.upstreams[idx]
            
            # Check if candidate has item available at output
            if candidate.get_output_item() is not None:
                # Update rr_index to NEXT position (for next tick)
                # This ensures we don't select the same upstream twice in a row
                self.rr_index = (idx + 1) % num_upstreams
                return candidate
        
        # No valid upstream found (all empty or blocked)
        # Still advance rr_index to maintain rotation fairness
        self.rr_index = (self.rr_index + 1) % num_upstreams
        return None

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: State Preparation
        
        Converger calculates next_buffer based on grants:
        1. If granted_to_downstream: buffer item will leave
        2. If granted_by_upstream: upstream item will enter buffer
        3. Both can happen (pass-through: buffer item out, upstream item in)
        
        Protocol Requirements:
        1. Fetch item from upstream using get_output_item() if granted
        2. Calculate next_buffer based on grants
        3. Do NOT mutate current buffer (happens in P4)
        4. All calculations write to next_buffer only
        
        State Table:
            | granted_out | granted_in | next_buffer   |
            |-------------|------------|---------------|
            | YES         | YES        | upstream_item |
            | YES         | NO         | None          |
            | NO          | YES        | upstream_item |
            | NO          | NO         | buffer        |
        
        Note:
            This is the DATA-FETCH phase. Items are fetched but not
            committed until Phase 4.
        """
        # Fetch item from upstream if granted (P3 data fetch)
        if self.granted_by_upstream and self.selected_upstream:
            self.upstream_item = self.selected_upstream.get_output_item()
        
        # Calculate next buffer state based on grants
        if self.granted_to_downstream:
            # Item will be transferred out from buffer
            if self.granted_by_upstream:
                # Item also coming in: pass-through (buffer stays occupied)
                self.next_buffer = self.upstream_item
            else:
                # Item going out, nothing coming in: buffer becomes empty
                self.next_buffer = None
        else:
            # No transfer out
            if self.granted_by_upstream:
                # Item coming in: buffer becomes occupied
                self.next_buffer = self.upstream_item
            else:
                # No change (stall)
                self.next_buffer = self.buffer

    def _phase_4_commit(self) -> None:
        """
        Phase 4: Atomic State Commit
        
        Swap buffer state. Reset transient state.
        
        Protocol Requirements:
        1. Swap next_buffer to buffer (atomic state change)
        2. Reset all transient state (granted flags, upstream_item, etc.)
        3. Reset visited_tick to -1 (for next tick's re-entry guard)
        4. Clear pending_requests list
        
        Note:
            rr_index is NOT reset here - it persists across ticks for
            deterministic round-robin arbitration.
            
            This is the only phase where buffer is mutated.
        """
        self.buffer = self.next_buffer
        
        # Reset transient state
        self.granted_by_upstream = False
        self.granted_to_downstream = False
        self.upstream_item = None
        self.selected_upstream = None
        self.visited_tick = -1
        self.pending_requests = []

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Checks if Converger has capacity to accept an item.
        
        Converger can accept if buffer is empty.
        
        Note:
            This is used by upstreams during Phase 2 to determine
            if they can grant items to this Converger.
        """
        return self.buffer is None

    def _get_capacity(self) -> int:
        """
        Returns the number of available slots in the buffer.
        """
        return 1 if self.buffer is None else 0

    def _can_accept_from_upstream(self) -> bool:
        """
        Determines if Converger can accept an item from upstream.
        
        Converger can accept from upstream if:
        1. Buffer is empty (can store item), OR
        2. Buffer is full BUT downstream is ready (can pass through)
        
        Note:
            This method extends _can_accept() by considering downstream state
            for pass-through optimization. This is critical for maximizing
            throughput when downstream is ready.
        
        Protocol Table:
            | downstream | buffer | request? |
            |------------|--------|----------|
            | ready      | empty  | YES      |
            | blocked    | empty  | YES      |
            | ready      | full   | YES      |
            | blocked    | full   | NO       |
        """
        if self.buffer is None:
            return True  # Empty buffer, always can accept
        
        # Buffer is full, check if we can pass through
        return self._has_ready_downstream()

    # Helper Methods - Grant & Transfer
    def _receive_grant(self, grantor: BaseComponent) -> None:
        """
        Called by upstream component during Phase 2 to signal a grant.
        
        This method notifies the Converger that its upstream has approved
        a transfer. The Converger will fetch the item in Phase 3.
        
        Note:
            Sets granted_by_upstream flag for Phase 3 item fetching.
            Does NOT fetch item here (happens in Phase 3).
        """
        self.granted_by_upstream = True

    def get_output_item(self) -> Optional[Item]:
        """
        Returns the item in buffer (available to downstreams).
        
        This method is called by downstream components during Phase 3
        to fetch items for their next_state calculation.
        
        Note:
            This is READ-ONLY. Does not mutate any state.
        """
        return self.buffer

    # Debug & Inspection Methods
    def _get_state_repr(self) -> str:
        """
        Returns a string representation of Converger state for debugging.
        """
        buffer_id = self.buffer.id if self.buffer else 0
        return f"Converger(buffer={buffer_id}, rr_index={self.rr_index})"

    def get_buffer(self) -> Optional[Item]:
        """
        Returns the current buffer state.
        
        Note:
            For debugging and inspection only.
        """
        return self.buffer