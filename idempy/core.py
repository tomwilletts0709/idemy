from typing import Any
import sys
import os
from datetime import datetime
from idempy.models import IdempotencyKey, Request
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
           
    def validate_request(self, request: dict[str, Any]) -> bool:
        if request is None:
            return False
        
        if request.headers.get('Idempotency-Key') is None:
            return False
        
        return True
    
    def validate_fingerprint(self, fingerprint: str) -> bool:
        if not isinstance(fingerprint, str) or not fingerprint: 
            return False
        
        if not fingerprint.strip(): 
            return False 
        
        return True
    
    

        
        


