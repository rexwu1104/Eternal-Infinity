from ..Imports import *

from .Song import MSong
from .Translator import MTranslator
from .Enum import MPlayMode, MPlayStatus

from random import randint
from typing_extensions import Self
from typing import TypeVar, Optional
from discord import Message, VoiceClient

__all__ = (
    'MContainer',
)

MusicView = TypeVar('MusicView') # from .View import MuiscView

class MContainer():
    client: VoiceClient = None
    data: list[MSong] = []
    dj_role_id: int
    guild_id: int
    info: list[dict] = []
    play_mode: MPlayMode = MPlayMode.Nothing
    now_pos: int = -1
    play_status: MPlayStatus = MPlayStatus.UnStarted
    range: Union[int, list[int], str] = None
    sent_message: Message = None
    source: MusicSource = None
    view: MusicView
    volume: float = 1.0
    translater: MTranslator
    
    def __init__(self, guild_id: int, translater: MTranslator) -> None:
        self.guild_id = guild_id
        self.translater = translater
        
    def clear(self) -> None:
        self.client = None
        self.data.clear()
        self.info.clear()
        self.play_mode = MPlayMode.Nothing
        self.now_pos = -1
        self.play_status = MPlayStatus.UnStarted
        self.range = None
        self.sent_message = None
        
    def __iter__(self) -> Self:
        return self
        
    def __next__(self) -> Optional[MSong]:
        if len(self) == 0: return None
        match self.play_mode:
            case MPlayMode.Nothing:
                if self.now_pos < len(self) - 1:
                    self.now_pos += 1
                else:
                    self.now_pos = -1
                    return None
                    
                return self.data[self.now_pos]
            
            case MPlayMode.Odd:
                return self.data[self.now_pos]
            
            case MPlayMode.Plural:
                if self.now_pos == self.range[1]:
                    self.now_pos = self.range[0]
                else:
                    self.now_pos += 1
                    
                return self.data[self.now_pos]
            
            case MPlayMode.All:
                if self.now_pos == len(self) - 1:
                    self.now_pos = 0
                else:
                    self.now_pos += 1
                    
                return self.data[self.now_pos]
            
            case MPlayMode.Shuffle:
                self.now_pos = randint(0, len(self) - 1)
                return self.data[self.now_pos]
            
    def __len__(self):
        return len(self.data)