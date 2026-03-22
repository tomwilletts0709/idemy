import pytest

from idempy.validator import ValidatedField, non_empty, min_value


class DummyString:
    name = ValidatedField(str, validators=(non_empty,))

    def __init__(self, name):
        self.name = name


class DummyInt:
    age = ValidatedField(int, validators=(min_value(10),))

    def __init__(self, age):
        self.age = age


class TestValidatedField:
    def test_valid_string(self):
        obj = DummyString("Tom")
        assert obj.name == "Tom"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            DummyString("   ")

    def test_valid_min_value(self):
        obj = DummyInt(15)
        assert obj.age == 15

    def test_min_value_raises(self):
        with pytest.raises(ValueError, match="age must be greater than 10"):
            DummyInt(5)