from .unit import Unit

class StorageBox(Unit):
    def __init__(self, name: str = '') -> None:
        super(StorageBox, self).__init__(6, name)