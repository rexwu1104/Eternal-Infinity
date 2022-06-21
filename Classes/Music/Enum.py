import enum

__all__ = (
    'MPlayMode',
    'MPlayStatus',
)

class MPlayMode(enum.Enum):
    Nothing = 0
    Odd = 1
    Plural = 2
    All = 3
    Shuffle = 4
    
class MPlayStatus(enum.Enum):
    UnStarted = 0
    Play = 1
    Pause = 2