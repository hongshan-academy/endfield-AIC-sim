# simulation/controller.py

from typing import List, Dict, Any, Optional
from .components.base import BaseComponent


class Controller:
    """
    Global simulation controller that orchestrates the 4-phase protocol.
    
    The Controller manages all components in the simulation graph and
    ensures deterministic execution through synchronized phase barriers.
    
    Protocol Phases per Global Tick:
        Phase 1: Request Propagation (Downstream → Upstream)
        Phase 2: Grant Resolution (Upstream → Downstream)
        Phase 3: State Preparation (Local calculation)
        Phase 4: Atomic Commit (Global state swap)
    
    Attributes:
        components: List of all components in the simulation graph.
        current_tick: Current global tick number (starts at 0).
        is_running: Flag indicating if simulation is active.
    """
    
    def __init__(self):
        """
        Initialize the Controller.
        
        Note:
            Components should be added via add_component() or set_components()
            before calling run() or step().
        """
        self.components: List[BaseComponent] = []
        self.current_tick: int = 0
        self.is_running: bool = False
    
    def add_component(self, component: BaseComponent) -> None:
        """
        Adds a component to the simulation graph.
        
        Args:
            component: The component to add.
        
        Note:
            Components should be connected via connect() before adding
            to ensure proper topology. set_context() will be called
            automatically when simulation starts.
        """
        if component not in self.components:
            self.components.append(component)
    
    def set_components(self, components: List[BaseComponent]) -> None:
        """
        Sets all components in the simulation graph.
        
        Args:
            components: List of all components in the simulation.
        
        Note:
            This replaces any existing components. Use for batch initialization.
        """
        self.components = components.copy()
    
    def initialize(self) -> None:
        """
        Initializes all components with context before simulation starts.
        
        This method must be called after all components are added and
        connected, but before run() or step() is called.
        
        Note:
            Calls set_context() on each component with reference to self.
        """
        for component in self.components:
            component.set_context(self)
    
    def step(self) -> int:
        """
        Executes one global tick (4 phases) of the simulation.
        
        Returns:
            The tick number that was just completed.
        
        Note:
            This is the core simulation loop. Each call advances the
            simulation by exactly one tick, ensuring deterministic behavior.
        
        Protocol Flow:
            1. Phase 1: All components execute _phase_1_request()
            2. Barrier: Wait for all P1 to complete
            3. Phase 2: All components execute _phase_2_grant()
            4. Barrier: Wait for all P2 to complete
            5. Phase 3: All components execute _phase_3_prepare()
            6. Barrier: Wait for all P3 to complete
            7. Phase 4: All components execute _phase_4_commit()
            8. Increment current_tick
        """
        # tick = self.current_tick
        
        # Phase 1: Request Propagation (Downstream → Upstream)
        # Each component recursively requests from upstreams
        for component in self.components:
            component._phase_1_request(self.current_tick, path_set=set())
        
        # Barrier 1: All P1 complete (implicit in synchronous execution)
        
        self.current_tick += 1
        # Phase 2: Grant Resolution (Upstream → Downstream)
        # Each component processes requests and issues grants
        for component in self.components:
            component._phase_2_grant(self.current_tick)
        
        # Barrier 2: All P2 complete (implicit in synchronous execution)
        
        # Phase 3: State Preparation (Local calculation)
        # Each component calculates next_state based on grants
        for component in self.components:
            component._phase_3_prepare()
        
        # Barrier 3: All P3 complete (implicit in synchronous execution)
        
        # Phase 4: Atomic Commit (Global state swap)
        # Each component commits next_state to current_state
        for component in self.components:
            component._phase_4_commit()
        
        # Increment tick counter
        self.current_tick += 1
        
        return self.current_tick
    
    def run(self, ticks: int) -> int:
        """
        Runs the simulation for a specified number of ticks.
        
        Args:
            ticks: Number of ticks to simulate.
        
        Returns:
            The final tick number after simulation completes.
        
        Note:
            Calls initialize() automatically if not already called.
            Sets is_running flag during execution.
        """
        # Initialize components if not already done
        if not all(hasattr(c, 'context') for c in self.components):
            self.initialize()
        
        self.is_running = True
        
        for _ in range(ticks):
            self.step()
        
        self.is_running = False
        return self.current_tick
    
    def reset(self) -> None:
        """
        Resets the simulation to initial state.
        
        Note:
            Calls _reset() on each component and resets current_tick to 0.
            Components remain in the graph and do not need to be re-added.
        """
        self.current_tick = 0
        self.is_running = False
        
        for component in self.components:
            component._reset()
    
    def get_component_by_type(self, component_type: type) -> List[BaseComponent]:
        """
        Returns all components of a specific type.
        
        Args:
            component_type: The class type to filter by (e.g., Conveyor, Splitter).
        
        Returns:
            List of components matching the specified type.
        
        Example:
            conveyors = controller.get_component_by_type(Conveyor)
        """
        return [c for c in self.components if isinstance(c, component_type)]
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Returns a snapshot of all component states for debugging.
        
        Returns:
            Dictionary mapping component type to list of state representations.
        
        Example:
            {
                'Source': ['Source(idx=0, next=Item(A, 1))'],
                'Conveyor': ['Conveyor(len=3, buffer=[1, 2, 3])'],
                'Sink': ['Sink(received=5)']
            }
        """
        snapshot = {}
        for component in self.components:
            comp_type = component.__class__.__name__
            if comp_type not in snapshot:
                snapshot[comp_type] = []
            snapshot[comp_type].append(component._get_state_repr())
        return snapshot
    
    def print_state(self) -> None:
        """
        Prints the current state of all components to console.
        
        Note:
            Useful for debugging and trace verification.
        """
        print(f"=== Tick {self.current_tick} ===")
        snapshot = self.get_state_snapshot()
        for comp_type, states in snapshot.items():
            for state in states:
                print(f"  {comp_type}: {state}")
        print()