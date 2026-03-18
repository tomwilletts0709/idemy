from typing import Any
import sys
import os
from datetime import datetime
from idempy.models import IdempotencyKey
from idempy.memory import MemoryStore



DEFAULT_SETTINGS = {
    'idempy_key_prefix': 'idempotency_key_',
    'IdempotencyKey': IdempotencyKey,
    'datetime_class': datetime,
    'stores': {
        'memory': MemoryStore(),
    },
}


class Core:
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = DEFAULT_SETTINGS
        self.stores = Stores(settings['stores'])
           
    def validate_request(self, idempotency_key: str) -> bool:
        if idempotency_key is None:
            return False
        
        if idempotency_key.strip(): 
            return False
        
        return True
        

        
        


