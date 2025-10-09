from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunnableEvent:
    pass


@dataclass(frozen=True, slots=True)
class Started(RunnableEvent):
    pass


@dataclass(frozen=True, slots=True)
class Progress(RunnableEvent):
    value: float


@dataclass(frozen=True, slots=True)
class Done(RunnableEvent):
    pass


@dataclass(frozen=True, slots=True)
class Cancelled(RunnableEvent):
    pass


@dataclass(frozen=True, slots=True)
class Failed(RunnableEvent):
    details: str
