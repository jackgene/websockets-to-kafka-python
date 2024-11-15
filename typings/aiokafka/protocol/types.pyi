from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union, overload
from typing_extensions import TypeAlias
from .abstract import AbstractType

T = TypeVar("T")
ValueT: TypeAlias = Union[Type[AbstractType[Any]], "String", "Array", "Schema"]
class Int8(AbstractType[int]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    


class Int16(AbstractType[int]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    


class Int32(AbstractType[int]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    


class UInt32(AbstractType[int]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    


class Int64(AbstractType[int]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    


class Float64(AbstractType[float]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: float) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> float:
        ...
    


class String:
    def __init__(self, encoding: str = ...) -> None:
        ...
    
    def encode(self, value: Optional[str]) -> bytes:
        ...
    
    def decode(self, data: BytesIO) -> Optional[str]:
        ...
    
    @classmethod
    def repr(cls, value: str) -> str:
        ...
    


class Bytes(AbstractType[Optional[bytes]]):
    @classmethod
    def encode(cls, value: Optional[bytes]) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> Optional[bytes]:
        ...
    
    @classmethod
    def repr(cls, value: Optional[bytes]) -> str:
        ...
    


class Boolean(AbstractType[bool]):
    _pack = ...
    _unpack = ...
    @classmethod
    def encode(cls, value: bool) -> bytes:
        ...
    
    @classmethod
    def decode(cls, data: BytesIO) -> bool:
        ...
    


class Schema:
    names: Tuple[str, ...]
    fields: Tuple[ValueT, ...]
    def __init__(self, *fields: Tuple[str, ValueT]) -> None:
        ...
    
    def encode(self, item: Sequence[Any]) -> bytes:
        ...
    
    def decode(self, data: BytesIO) -> Tuple[Union[Any, str, None, List[Union[Any, Tuple[Any, ...]]]], ...]:
        ...
    
    def __len__(self) -> int:
        ...
    
    def repr(self, value: Any) -> str:
        ...
    


class Array:
    array_of: ValueT
    @overload
    def __init__(self, array_of_0: ValueT) -> None:
        ...
    
    @overload
    def __init__(self, array_of_0: Tuple[str, ValueT], *array_of: Tuple[str, ValueT]) -> None:
        ...
    
    def __init__(self, array_of_0: Union[ValueT, Tuple[str, ValueT]], *array_of: Tuple[str, ValueT]) -> None:
        ...
    
    def encode(self, items: Optional[Sequence[Any]]) -> bytes:
        ...
    
    def decode(self, data: BytesIO) -> Optional[List[Union[Any, Tuple[Any, ...]]]]:
        ...
    
    def repr(self, list_of_items: Optional[Sequence[Any]]) -> str:
        ...
    


class UnsignedVarInt32(AbstractType[int]):
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    


class VarInt32(AbstractType[int]):
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    


class VarInt64(AbstractType[int]):
    @classmethod
    def decode(cls, data: BytesIO) -> int:
        ...
    
    @classmethod
    def encode(cls, value: int) -> bytes:
        ...
    


class CompactString(String):
    def decode(self, data: BytesIO) -> Optional[str]:
        ...
    
    def encode(self, value: Optional[str]) -> bytes:
        ...
    


class TaggedFields(AbstractType[Dict[int, bytes]]):
    @classmethod
    def decode(cls, data: BytesIO) -> Dict[int, bytes]:
        ...
    
    @classmethod
    def encode(cls, value: Dict[int, bytes]) -> bytes:
        ...
    


class CompactBytes(AbstractType[Optional[bytes]]):
    @classmethod
    def decode(cls, data: BytesIO) -> Optional[bytes]:
        ...
    
    @classmethod
    def encode(cls, value: Optional[bytes]) -> bytes:
        ...
    


class CompactArray(Array):
    def encode(self, items: Optional[Sequence[Any]]) -> bytes:
        ...
    
    def decode(self, data: BytesIO) -> Optional[List[Union[Any, Tuple[Any, ...]]]]:
        ...
    


