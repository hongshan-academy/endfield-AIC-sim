from typing import List, Optional, TYPE_CHECKING
from .base import BaseComponent
from ..item import Item

if TYPE_CHECKING:
    pass


class Converger(BaseComponent):
    def __init__(self) -> None:
        super().__init__()

    def _can_push_to_downstream(self) -> bool:
        # Converger can push if it has an item
        return self.buffer is not None

    def get_buffer(self) -> List[Optional[Item]]:
        return [self.buffer]