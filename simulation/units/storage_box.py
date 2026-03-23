from .unit import Unit

class StorageBox(Unit):
    NEED_ADJUDICATION = True
    
    def __init__(self, name: str = '') -> None:
        super(StorageBox, self).__init__(6, name)
    
    def __str__(self) -> str:
        return 'StorageBox(%s)' % self._inventory.__str__()[1:-1]