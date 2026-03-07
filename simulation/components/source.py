from typing import List, Optional, TYPE_CHECKING
from .base import BaseComponent
from ..item import Item

if TYPE_CHECKING:
    pass


class Source(BaseComponent):
    def __init__(self, items: List[Item]) -> None:
        super().__init__()
        self.items = items.copy()
        self.items_to_generate = items.copy()

    def _can_push_to_downstream(self) -> bool:
        # Source can always try to push if it has items to generate
        return len(self.items_to_generate) > 0

    def _phase_1_request(self, path: set) -> bool:
        # Cycle detection
        if self in path:
            return False
        # Check if we want to push
        if not self._can_push_to_downstream():
            return False
        # Request downstream
        for ds in self.downstream_components:
            new_path = path | {self}
            if not ds._phase_1_request(new_path):
                return False
        return True

    def _phase_3_compute(self) -> None:
        # Calculate next_state
        if self.acknowledged_by_downstream and len(self.items_to_generate) > 0:
            # Generate and push new item
            item = self.items_to_generate.pop(0)
            self._push_output_item(item)

    def _push_output_item(self, item: Item) -> None:
        for ds in self.downstream_components:
            if hasattr(ds, '_receive_item') and ds._can_accept():
                ds._receive_item(item)
                break

    def get_buffer(self) -> List[Optional[Item]]:
        # Source doesn't have a buffer, return empty
        return []