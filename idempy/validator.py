from typing import Any, Callable

type Validator = Callable[[str, Any], None]

def non_empty(field: str, value: Any) -> None: 
    if not isinstance(value, str) or not value.strip(): 
        raise ValueError(f'{field} cannot be empty')

def min_value(n:int) -> Validator:
    def _v(field: str, value: Any) -> None:
        if value < n: 
            raise ValueError(f'{field} must be greater than {n}')
    return _v

class VaidatedField[T]:
    def __init__(self, cast: Callable[[Any], T], value: T, validators: tuple[Validator, ...]) -> None:
        self.cast    = cast
        self.validators = validators
        self.name: str = ""
        self.storage_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.storage_name = f"_{name}"

    def __get__(self, instance: object | None, owner: type) -> Any:
        if instance is None: 
            return self
        return getattr(instance, self.storage_name)

    def __set__(self, instance: object, value: Any) -> None:
        casted = self.cast(value)
        for v in self.validators:
            v(self.name, casted)
        setattr(instance, self.storage_name, casted)
    

    