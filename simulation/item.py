from typing import Any

class Item:
    """
    Immutable payload representing an item on the conveyor system.
    """
    def __init__(self, name: str, item_id: int):
        self.name: str = name
        self.id: int = item_id

    def __repr__(self) -> str:
        return f"Item({self.name}, {self.id})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Item):
            return False
        return self.id == other.id and self.name == other.name

    def __hash__(self) -> int:
        return hash((self.name, self.id))
