from ..Imports import *

import orjson as json

from typing import Callable

class MDB():
    read: Callable[[str], JSON]
    write: Callable[[str, JSON], None]
    
    def read(self, path: str) -> JSON:
        with open(path, 'r', encoding='utf-8') as rfile:
            return json.loads(rfile.read())
        
    def write(self, path: str, data: JSON) -> None:
        data = dict([(str(k), v) for k, v in data.items()])
        with open(path, 'w', encoding='utf-8') as wfile:
            wfile.write(json.dumps(data).decode())