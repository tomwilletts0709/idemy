from pytest import fixture
from idempy.stores import Stores
from idempy.memory import MemoryStore

@fixture
def stores():
    return Stores(stores={'memory': MemoryStore()})

def test_get_store(stores):
    assert stores.get('memory') is not None

def test_get_store_default(stores):
    assert stores.get('default') is not None

def test_get_store_not_found(stores):
    with pytest.raises(ValueError, match="Store default not found"):
        stores.get('not_found')