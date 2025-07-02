from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Dado(_message.Message):
    __slots__ = ("conteudo",)
    CONTEUDO_FIELD_NUMBER: _ClassVar[int]
    conteudo: str
    def __init__(self, conteudo: _Optional[str] = ...) -> None: ...

class Consulta(_message.Message):
    __slots__ = ("chave",)
    CHAVE_FIELD_NUMBER: _ClassVar[int]
    chave: str
    def __init__(self, chave: _Optional[str] = ...) -> None: ...

class Resposta(_message.Message):
    __slots__ = ("mensagem", "conteudo")
    MENSAGEM_FIELD_NUMBER: _ClassVar[int]
    CONTEUDO_FIELD_NUMBER: _ClassVar[int]
    mensagem: str
    conteudo: str
    def __init__(self, mensagem: _Optional[str] = ..., conteudo: _Optional[str] = ...) -> None: ...

class LogEntry(_message.Message):
    __slots__ = ("epoca", "offset", "conteudo")
    EPOCA_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    CONTEUDO_FIELD_NUMBER: _ClassVar[int]
    epoca: int
    offset: int
    conteudo: str
    def __init__(self, epoca: _Optional[int] = ..., offset: _Optional[int] = ..., conteudo: _Optional[str] = ...) -> None: ...

class CommitRequest(_message.Message):
    __slots__ = ("epoca", "offset")
    EPOCA_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    epoca: int
    offset: int
    def __init__(self, epoca: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("sucesso", "mensagem")
    SUCESSO_FIELD_NUMBER: _ClassVar[int]
    MENSAGEM_FIELD_NUMBER: _ClassVar[int]
    sucesso: bool
    mensagem: str
    def __init__(self, sucesso: bool = ..., mensagem: _Optional[str] = ...) -> None: ...

class EstadoReplica(_message.Message):
    __slots__ = ("epoca", "offset")
    EPOCA_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    epoca: int
    offset: int
    def __init__(self, epoca: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class EntradasParaSincronizar(_message.Message):
    __slots__ = ("entradas",)
    ENTRADAS_FIELD_NUMBER: _ClassVar[int]
    entradas: _containers.RepeatedCompositeFieldContainer[LogEntry]
    def __init__(self, entradas: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...
