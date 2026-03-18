# ITEM_STACK_CAPACITY = 50

# from .item import Item
# from .exception import ItemTypeError, ItemStackFullError, ItemStackEmptyError
# from typing import Callable

# def assert_valid(func: Callable, *args, **kwargs):
#     item_stack = args[0]
#     assert 0 <= item_stack._count <= item_stack.capacity

#     return func(*args, **kwargs)

# class ItemStack(object):
#     name: str
#     capacity: int
    
#     _count: int
    
#     def __init__(self, name: str, capacity: int = ITEM_STACK_CAPACITY, count: int = 0) -> None:
#         self.name = name
#         self.capacity = capacity
#         self._count = count
    
#     def push(self, item: Item):
#         if item.name != self.name:
#             raise ItemTypeError('%s != %s' % (item.name, self.name))
#         if self._count >= self.capacity:
#             raise ItemStackFullError()
        
#         self._count += 1
    
#     def pop(self) -> Item:
#         if self._count <= 0:
#             raise ItemStackEmptyError()
        
#         self._count -= 1
#         return Item(self.name, self._count)
    
#     def can_pop(self) -> bool:
#         return self._count > 0
    
#     def can_push(self) -> bool:
#         return self._count < self.capacity
    
#     def is_full(self) -> bool:
#         return self._count >= self.capacity
    
#     @assert_valid
#     def is_empty(self) -> bool:
#         return self._count <= 0
    