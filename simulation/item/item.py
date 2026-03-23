# from functools import total_ordering


# @total_ordering
class Item(object):
    def __init__(self, type: str, item_id: int = 0) -> None:
        self.type = type
        self.id   = item_id
        # self.life_time = 0
    
    def __repr__(self) -> str:
        return str(self)
    
    def __str__(self) -> str:
        if self.type:
            return f'Item.{self.type}({self.id})'
        else:
            return f'Item({self.id})'
    
    def __hash__(self) -> int:
        return hash((self.type, self.id))
    
    # def reset_life_time(self):
    #     self.life_time = 0
    
    # def tick(self):
    #     self.life_time += 1
    
    # def __eq__(self, value: object) -> bool:
    #     if isinstance(value, Item):
    #         return self.life_time == value.life_time
        
    #     raise ValueError(value)

    # def __lt__(self, value: object) -> bool:
    #     if isinstance(value, Item):
    #         return self.life_time < value.life_time
        
    #     raise ValueError(value)

