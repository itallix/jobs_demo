from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    pass


@dataclass(frozen=True, slots=True)
class Started(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Progress(ExecutionEvent):
    value: float


@dataclass(frozen=True, slots=True)
class Done(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Cancelled(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Failed(ExecutionEvent):
    details: str
