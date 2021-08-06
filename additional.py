import enum
from collections import defaultdict


class ItemSelection(enum.Enum):
    # selection constants
    CLEAR = 0
    PREVIOUS = 1
    NEXT = 2

    @staticmethod
    def selector():
        switcher = defaultdict(lambda pos: lambda: -1,
                               {ItemSelection.CLEAR: lambda pos: -1,
                                ItemSelection.PREVIOUS: lambda pos: pos - 1,
                                ItemSelection.NEXT: lambda pos: pos + 1})
        return switcher

