ITEM_STACK_CAPACITY = 50

from .item import Item
from .exception import ItemTypeError, ItemStackFullError, ItemStackEmptyError


class ItemStack(object):
    item_type: str
    capacity: int
    
    _count: int
    
    def __init__(self, item_type: str, capacity: int = ITEM_STACK_CAPACITY, count: int = 0) -> None:
        self.item_type = item_type
        self.capacity = capacity
        self._count = count
    
    def push(self, item: Item):
        if item.type != self.item_type:
            raise ItemTypeError('%s != %s' % (item.type, self.item_type))
        if self._count >= self.capacity:
            raise ItemStackFullError()
        
        self._count += 1
    
    def pop(self) -> Item:
        if self._count <= 0:
            raise ItemStackEmptyError()
        
        self._count -= 1
        return Item(self.item_type, self._count)
    
    def can_pop(self) -> bool:
        return self._count > 0
    
    def can_push(self) -> int:
        return self.capacity - self._count
    
    def is_full(self) -> bool:
        return self._count >= self.capacity
    
    def is_empty(self) -> bool:
        return self._count <= 0
    