from typing import List, Optional, Set, Any


class BaseComponent(object):
    # Class-Level Variable Declarations
    context: Any
    upstreams: List["BaseComponent"]
    downstreams: List["BaseComponent"]
    visited_tick: int
    pending_requests: List["BaseComponent"]

    # Lifecycle & Initialization
    def __init__(self):
        """
        Direct instantiation is forbidden.
        
        Subclasses must implement their own __init__ to initialize
        component-specific state, then call set_context() for protocol
        state initialization.
        """
        raise NotImplementedError

    def set_context(self, context: Any) -> None:
        """
        Injects the global simulation context and initializes protocol state.
        
        This method must be called by the Controller before simulation starts.
        It initializes all transient state variables used by the 4-phase protocol.
        
        Note:
            Subclasses should call super().set_context(context) first,
            then initialize their own component-specific state.
        """
        self.context = context
        self.visited_tick = -1
        self.pending_requests = []
        # self.downstreams = []

    def connect(self, upstreams: List["BaseComponent"]) -> None:
        """
        Establishes network topology by setting upstream connections.
        
        This method creates bidirectional links:
        - Sets self.upstreams to the provided list
        - Registers self as a downstream to each upstream component
        
        Note:
            This method should be called during network construction,
            before set_context() is called by the Controller.
        """
        self.upstreams = upstreams
        for up in upstreams:
            if not hasattr(up, 'downstreams') or up.downstreams is None:
                up.downstreams = []
            up.downstreams.append(self)

    # Protocol Phase Methods
    def _phase_1_request(self, tick: int, path_set: Set["BaseComponent"]) -> None:
        """
        Phase 1: Recursive Request Propagation (Downstream → Upstream)
        
        This phase propagates pull signals upstream. Components request
        capacity from their upstreams if they can accept items.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick) to prevent double execution
        2. Check cycle detection (path_set) to prevent infinite recursion
        3. Add self to upstream.pending_requests before calling upstream
        4. Recursively call upstream._phase_1_request()
        5. Do NOT mutate any persistent state
        
        Note:
            This is a READ-ONLY phase. No state mutation allowed.
        """
        raise NotImplementedError

    def _phase_2_grant(self, tick: int) -> None:
        """
        Phase 2: Recursive Grant Resolution (Upstream → Downstream)
        
        This phase propagates grant signals downstream. Components that
        received requests in P1 decide which downstreams to grant.
        
        Protocol Requirements:
        1. Check re-entry guard (visited_tick) to prevent double execution
        2. Process pending_requests from downstreams
        3. Perform arbitration if multiple downstreams requested
        4. Call downstream._receive_grant() for selected downstreams
        5. Do NOT fetch items (get_output_item) in this phase
        6. Do NOT mutate persistent state
        
        Note:
            This is a CONTROL-ONLY phase. No data transfer allowed.
            Item fetching happens in Phase 3.
        """
        raise NotImplementedError

    def _phase_3_prepare(self) -> None:
        """
        Phase 3: Local State Preparation
        
        This phase calculates next_state based on grants received in P2.
        Components fetch items from upstreams and prepare buffer shifts.
        
        Protocol Requirements:
        1. Fetch items from upstream using get_output_item() if granted
        2. Calculate next_state (e.g., next_buffer) based on grants
        3. Do NOT mutate current_state (e.g., buffer)
        4. All calculations write to next_state variables only
        
        Note:
            This is the DATA-FETCH phase. Items are fetched but not
            committed until Phase 4.
        """
        raise NotImplementedError

    def _phase_4_commit(self) -> None:
        """
        Phase 4: Atomic State Commit
        
        This phase atomically swaps next_state to current_state.
        All components commit simultaneously for deterministic behavior.
        
        Protocol Requirements:
        1. Swap next_state to current_state (e.g., buffer = next_buffer)
        2. Reset all transient state (granted flags, upstream_item, etc.)
        3. Reset visited_tick to -1 (for next tick's re-entry guard)
        4. Clear pending_requests list
        5. Do NOT fetch items or make grants in this phase
        
        Note:
            This is the only phase where current_state is mutated.
            After this phase, all state changes are visible to next tick.
        """
        raise NotImplementedError

    # Helper Methods - Capacity & Acceptance
    def _can_accept(self) -> bool:
        """
        Checks if this component has capacity to accept an item.
        
        This method is called by upstreams during Phase 2 to determine
        if a grant can be issued.
        
        Note:
            Default implementation returns False. Subclasses must override
            based on their buffer/capacity logic.
        
        Examples:
            - Conveyor: True if output slot (buffer[-1]) is None
            - Splitter: True if buffer is None
            - Sink: Always True (infinite capacity)
            - Source: Always False (no input capacity)
        """
        return False

    def _get_capacity(self) -> int:
        """
        Returns the number of available slots for accepting items.
        
        This method is used for debugging and capacity queries.
        
        Note:
            Default implementation returns 0. Subclasses must override
            based on their buffer implementation.
        """
        return 0

    def _can_accept_from_upstream(self) -> bool:
        """
        Determines if this component can accept an item from upstream.
        
        This method extends _can_accept() by considering downstream state
        for pass-through optimization. Components with buffers can accept
        from upstream if:
        1. Buffer is empty (can store item), OR
        2. Buffer is full BUT downstream is ready (can pass through)
        
        Note:
            Default implementation delegates to _can_accept().
            Splitter and Converger should override to check downstream state.
        
        Protocol Table:
            | downstream | buffer | request? |
            |------------|--------|----------|
            | ready      | empty  | YES      |
            | blocked    | empty  | YES      |
            | ready      | full   | YES      |
            | blocked    | full   | NO       |
        """
        return self._can_accept()

    def _has_ready_downstream(self) -> bool:
        """
        Checks if any downstream component is ready to receive items.
        
        This method is used by Splitter and Converger to determine
        pass-through capability in _can_accept_from_upstream().
        
        Note:
            Default implementation checks pending_requests and _can_accept()
            for each downstream. This is sufficient for most components.
        """
        for down in self.downstreams:
            if down in self.pending_requests and down._can_accept():
                return True
        return False

    # Helper Methods - Grant & Transfer
    def _receive_grant(self, grantor: "BaseComponent") -> None:
        """
        Called by upstream component during Phase 2 to signal a grant.
        
        This method notifies the component that its upstream has approved
        a transfer. The component should set internal flags to prepare
        for item fetching in Phase 3.
        
        Args:
            grantor: The upstream component that issued the grant.
        
        Note:
            Default implementation does nothing. Subclasses should override
            to set granted_by_upstream = True or similar flags.
            
            Do NOT fetch items in this method. Item fetching happens in
            Phase 3 via get_output_item().
        """
        pass

    def get_output_item(self) -> Optional[Any]:
        """
        Returns the item available at this component's output port.
        
        This method is called by downstream components during Phase 3
        to fetch items for their next_state calculation.
        
        Returns:
            The item at the output port, or None if no item available.
        
        Note:
            Default implementation returns None. Subclasses must override
            to return their output item (e.g., buffer[-1] for Conveyor,
            buffer for Splitter/Converger, next_item for Source).
            
            This method should be READ-ONLY. Do not mutate state.
        """
        return None

    # Debug & Inspection Methods
    def _get_state_repr(self) -> str:
        """
        Returns a string representation of component state for debugging.
        
        Returns:
            Human-readable string describing current component state.
        
        Note:
            Default implementation returns class name. Subclasses should
            override to include buffer contents, indices, etc.
        """
        return self.__class__.__name__

    def _reset(self) -> None:
        """
        Resets component to initial state (for simulation restart).
        
        This method is called by the Controller when restarting a simulation.
        
        Note:
            Default implementation resets protocol state only. Subclasses
            should override to reset component-specific state (buffers,
            indices, counters, etc.).
        """
        self.visited_tick = -1
        self.pending_requests = []