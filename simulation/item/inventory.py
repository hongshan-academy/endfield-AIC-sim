from typing import List, Dict, Optional
from .item import Item
from .exception import ItemTypeError
from .item_stack import ItemStack, ITEM_STACK_CAPACITY

class Inventory(object):
    _inventory: List[Optional[ItemStack]]
    _capacity:  int
    
    def __init__(self, capacity: int) -> None:
        self._inventory = [None] * capacity
        self._capacity  = capacity
        
    def can_push(self, item_type: str) -> int:
        # 1. has empty item stack
        # 2. has item & c < 50
        # TODO: 对于情况 [50, 50, 50, 50, 49, 0] 时输入两个不同物品时它的表现？
        
        c = 0
        for item_stack in self._inventory:
            if item_stack is None:
                c += ITEM_STACK_CAPACITY
            elif item_stack.item_type == item_type:
                c += ITEM_STACK_CAPACITY - item_stack._count
            
        return c
                    
    def can_pop(self, item_type: str) -> bool:
        for item_stack in self._inventory:
            if item_stack is not None and item_stack.item_type == item_type:
                if item_stack.can_pop():
                    return True
        return False
    
    def has_item(self) -> bool:
        return any(item_stack is not None for item_stack in self._inventory)
    
    def push(self, item: Item) -> None:
        for i, item_stack in enumerate(self._inventory):
            if item_stack is None:
                self._inventory[i] = ItemStack(item.type, count=1)
                return
            elif item_stack.item_type == item.type:
                if item_stack.can_push():
                    item_stack.push(item)
                    return
        
        raise ItemTypeError(item)

    def pop(self) -> Optional[Item]:
        for i, item_stack in enumerate(self._inventory):
            if item_stack is None:
                continue
            if not item_stack.can_pop():
                continue
            
            item = item_stack.pop()
            if not item_stack.can_pop():
                self._inventory[i] = None
            return item
    
        return None
    
    def remaining_capacity(self) -> Dict[str, int]:
        types = set()
        for stack in self._inventory:
            if stack is not None:
                types.add(stack.item_type)
        return {typ: self.can_push(typ) for typ in types}