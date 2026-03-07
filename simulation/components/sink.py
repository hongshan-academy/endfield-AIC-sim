from typing import List, Optional, TYPE_CHECKING
from .base import BaseComponent
from ..item import Item

if TYPE_CHECKING:
    pass


class Sink(BaseComponent):
    def __init__(self) -> None:
        super().__init__()
        self.items_received = 0
        self.received_items: List[Item] = []

    def _can_push_to_downstream(self) -> bool:
        # Sink cannot push to downstream (it's the end)
        return False

    def _phase_3_compute(self) -> None:
        # Calculate next_state
        if self.acknowledged_by_downstream and self.buffer is not None:
            # Accept the item
            self.received_items.append(self.buffer)
            self.items_received += 1
            self.next_buffer = None

    def get_buffer(self) -> List[Optional[Item]]:
        return [self.buffer]