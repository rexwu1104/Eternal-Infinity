from ..Imports import *

__all__ = (
    'MTranslator',
)

class MTranslator():
    data: dict[str, dict[str, str]] = get_translation_data()
    i18n: str
    
    def __init__(self, i18n: str) -> None:
        self.i18n = i18n
        
    def translate(self, content: str) -> str:
        return self.data[self.i18n][content]