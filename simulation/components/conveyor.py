from typing import List, Optional, TYPE_CHECKING
from .base import BaseComponent
from ..item import Item

if TYPE_CHECKING:
    pass


class Conveyor(BaseComponent):
    def __init__(self, length: int = 1) -> None:
        super().__init__()
        self.length = length
        self.buffer_items: List[Optional[Item]] = [None] * length

    def _can_push_to_downstream(self) -> bool:
        # Conveyor can push if it has an item at the output end
        return self.buffer_items[-1] is not None

    def _phase_3_compute(self) -> None:
        # Calculate next_state
        if self.acknowledged_by_downstream and self.buffer_items[-1] is not None:
            self._push_output_item()
            # Shift all items forward
            for i in range(self.length - 1):
                self.buffer_items[i] = self.buffer_items[i + 1] if i < self.length - 1 else None
            self.buffer_items[-1] = None

    def _push_output_item(self) -> None:
        # Push the last item to downstream
        item_to_push = self.buffer_items[-1]
        for ds in self.downstream_components:
            if ds.buffer is None or (hasattr(ds, 'buffer_items') and ds._can_accept()):
                if hasattr(ds, 'buffer_items'):
                    ds._receive_item(item_to_push)
                else:
                    ds.next_buffer = item_to_push
                self.buffer_items[-1] = None
                break

    def _can_accept(self) -> bool:
        return self.buffer_items[0] is None

    def _receive_item(self, item: Item) -> None:
        self.buffer_items[0] = item

    def get_buffer(self) -> List[Optional[Item]]:
        return self.buffer_items

    def has_item(self) -> bool:
        return any(item is not None for item in self.buffer_items)