from typing import List, Tuple, Optional
from .item import Item

class Inventory(object):
    _inventory: List[Tuple[Optional[str], int]]
    
    def __init__(self, capacity: int) -> None:
        self._inventory = [
            (None, 0) for _ in range(capacity)
        ]
        
    def can_add(self, item_name: str) -> int:
        # 1. has empty item stack
        # 2. has item & c < 50
        for k, v in self._inventory:
            if k is None:
                return 50
            elif 0 <= v < 50:
                return 50 - v
        
        return 0
                    
    def can_pop(self, item_name: str) -> bool:
        for k, v in self._inventory:
            if k == item_name:
                return 0 < v <= 50
        
        return False
    
    def add(self, item: Item) -> None:
        for i, (name, count) in enumerate(self._inventory):
            if name is None:
                self._inventory[i] = (item.name, 1)
                return
            elif name == item.name and count < 50:
                self._inventory[i] = (name, count + 1)
                return
    
    def pop(self) -> Optional[Item]:
        for i, (name, count) in enumerate(self._inventory):
            if name is not None and count > 0:
                self._inventory[i] = (
                    (name, count - 1) if count - 1 > 0 else (None, 0)
                )
                return Item(name)
        
        return None
                