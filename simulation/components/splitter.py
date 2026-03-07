from typing import List, Optional, Set, Any
from ..item import Item
from .base import BaseComponent


class Splitter(BaseComponent):
    # Splitter-specific state
    buffer: Optional[Item]
    next_buffer: Optional[Item]
    rr_index: int
    granted_by_upstream: bool
    granted_downstream: Optional[BaseComponent]
    upstream_item: Optional[Item]

    # Lifecycle & Initialization
    def __init__(self, num_outputs: int):
        """
        Splitter initialization.
        
        Note:
            Splitter has a 1-slot buffer with 1-tick latency.
            Items always enter buffer first, then exit on next tick (no bypass).
            Round-robin ensures fair distribution across downstreams.
            Blocked downstreams are skipped in the rotation.
        """
        self.buffer = None
        self.next_buffer = None
        self.rr_index = 0
        self.granted_by_upstream = False
        self.granted_downstream = None
        self.upstream_item = None
        self._num_outputs = num_outputs

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
        Resets Splitter to initial state for simulation restart.
        """
        super()._reset()
        self.buffer = None
        self.next_buffer = None
        self.rr_index = 0
        self.granted_by_upstream = False
        self.granted_downstream = None
        self.upstream_item = None

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set[BaseComponent]) -> None:
        """
        Phase 1: Request Propagation (Downstream → Upstream)
        
        Splitter requests from upstream if it can accept items.
        Splitter can accept if:
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
        # Splitter can accept if buffer empty OR downstream ready (pass-through)
        if self._can_accept_from_upstream() and self.upstreams:
            for up in self.upstreams:
                if self not in up.pending_requests:
                    up.pending_requests.append(self)
                # Recurse upstream
                up._phase_1_request(tick, new_path)

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Grant Resolution (Upstream → Downstream)
        
        Splitter performs round-robin arbitration over downstreams that
        requested items. Blocked downstreams are skipped in the rotation.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick)
        2. Process pending_requests from downstreams
        3. Perform round-robin arbitration to select one downstream
        4. Skip blocked downstreams (not in pending_requests or !_can_accept())
        5. Call downstream._receive_grant() for selected downstream
        6. Do NOT fetch items in this phase (happens in P3)
        7. Update rr_index for deterministic distribution
        
        Round-Robin Example (3 downstreams, #3 blocked):
            Tick 1: rr_index=0 → Select #1, rr_index→1
            Tick 2: rr_index=1 → Select #2, rr_index→2
            Tick 3: rr_index=2 → Skip #3 (blocked), rr_index→0, Select #1
            Tick 4: rr_index=1 → Select #2, rr_index→2
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
        self.granted_downstream = None
        self.upstream_item = None
        
        # Arbitration: Select downstream from pending_requests using round-robin
        if self.buffer is not None and self.pending_requests:
            selected_downstream = self._select_downstream_round_robin()
            
            if selected_downstream and selected_downstream._can_accept():
                self.granted_downstream = selected_downstream
                # Notify downstream of grant (control signal only)
                selected_downstream._receive_grant(self)
        
        # Note: Upstream will call our _receive_grant() if they grant
        # This happens in upstream's _phase_2_grant() method

    def _select_downstream_round_robin(self) -> Optional[BaseComponent]:
        """
        Selects a downstream using round-robin arbitration.
        
        Only considers downstreams that:
        1. Have made requests (in pending_requests)
        2. Can accept items (_can_accept() returns True)
        
        Blocked downstreams are SKIPPED in the rotation, but rr_index
        still advances past them to maintain fair distribution.
        
        Example (3 downstreams, #3 blocked):
            downstreams = [D1, D2, D3]
            rr_index = 0
            
            Tick 1: Start at 0 → D1 requested? YES, can_accept? YES → Select D1, rr_index→1
            Tick 2: Start at 1 → D2 requested? YES, can_accept? YES → Select D2, rr_index→2
            Tick 3: Start at 2 → D3 requested? YES, can_accept? NO → Skip, rr_index→0
                    Continue at 0 → D1 requested? YES, can_accept? YES → Select D1, rr_index→1
            Pattern: D1 → D2 → D1 → D2 → ... (D3 skipped)
        
        Note:
            This method is extracted for future modification.
            Alternative arbitration strategies can be implemented here:
            - Priority-based selection
            - Weighted round-robin
            - Least-recently-used
            - Buffer-level aware selection
        """
        if not self.pending_requests:
            return None
        
        num_downstreams = len(self.downstreams)
        if num_downstreams == 0:
            return None
        
        # Start from rr_index and search for a valid downstream
        # We may need to wrap around multiple times if many are blocked
        for i in range(num_downstreams):
            idx = (self.rr_index + i) % num_downstreams
            candidate = self.downstreams[idx]
            
            # Check if candidate requested AND can accept
            if candidate in self.pending_requests and candidate._can_accept():
                # Update rr_index to NEXT position (for next tick)
                # This ensures we don't select the same downstream twice in a row
                self.rr_index = (idx + 1) % num_downstreams
                return candidate
        
        # No valid downstream found (all blocked or no requests)
        # Still advance rr_index to maintain rotation fairness
        self.rr_index = (self.rr_index + 1) % num_downstreams
        return None

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: State Preparation
        
        Splitter calculates next_buffer based on grants:
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
        if self.granted_by_upstream and self.upstreams:
            self.upstream_item = self.upstreams[0].get_output_item()
        
        # Calculate next buffer state based on grants
        if self.granted_downstream is not None:
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
        self.granted_downstream = None
        self.upstream_item = None
        self.visited_tick = -1
        self.pending_requests = []

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Checks if Splitter has capacity to accept an item.
        
        Splitter can accept if buffer is empty.
        
        Note:
            This is used by upstreams during Phase 2 to determine
            if they can grant items to this Splitter.
        """
        return self.buffer is None

    def _get_capacity(self) -> int:
        """
        Returns the number of available slots in the buffer.
        """
        return 1 if self.buffer is None else 0

    def _can_accept_from_upstream(self) -> bool:
        """
        Determines if Splitter can accept an item from upstream.
        
        Splitter can accept from upstream if:
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
        
        This method notifies the Splitter that its upstream has approved
        a transfer. The Splitter will fetch the item in Phase 3.
        
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
        Returns a string representation of Splitter state for debugging.
        """
        buffer_id = self.buffer.id if self.buffer else 0
        return f"Splitter(buffer={buffer_id}, rr_index={self.rr_index})"

    def get_buffer(self) -> Optional[Item]:
        """
        Returns the current buffer state.
        
        Note:
            For debugging and inspection only.
        """
        return self.buffer