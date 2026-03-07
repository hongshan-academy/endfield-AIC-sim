from typing import List, Optional, TYPE_CHECKING
from .base import BaseComponent
from ..item import Item

if TYPE_CHECKING:
    pass


class Splitter(BaseComponent):
    def __init__(self) -> None:
        super().__init__()

    def _can_push_to_downstream(self) -> bool:
        # Splitter can push if it has an item
        return self.buffer is not None

    def _push_output_item(self) -> None:
        # Push to first available downstream
        for ds in self.downstream_components:
            if ds.buffer is None:
                ds.next_buffer = self.buffer
                self.next_buffer = None
                break

    def get_buffer(self) -> List[Optional[Item]]:
        return [self.buffer]