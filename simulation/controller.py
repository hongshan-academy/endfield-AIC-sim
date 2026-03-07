from typing import List, Optional
from .components import Source, Sink, Conveyor, Splitter, Converger
from .item import Item


class Controller:
    def __init__(self) -> None:
        self.components: List = []

    def set_components(self, components: List) -> None:
        self.components = components

    def initialize(self) -> None:
        # Reset all components state
        for comp in self.components:
            comp.visited = False
            comp.acknowledged_by_downstream = False
            comp.path = set()
            comp.next_buffer = None

    def step(self) -> None:
        # Phase 1: Request (upstream to downstream)
        for comp in self.components:
            comp._phase_1_request(set())

        # Phase 2: Response (downstream to upstream)
        for comp in reversed(self.components):
            comp._phase_2_response()

        # Phase 3: Compute
        for comp in self.components:
            comp._phase_3_compute()

        # Phase 4: Update
        for comp in self.components:
            comp._phase_4_update()

    def print_state(self) -> None:
        for comp in self.components:
            print(f"{comp.__class__.__name__}: buffer={comp.get_buffer()}")
        print("---")