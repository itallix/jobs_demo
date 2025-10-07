from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrainingEvent:
    pass


@dataclass(frozen=True, slots=True)
class Progress(TrainingEvent):
    value: float


@dataclass(frozen=True, slots=True)
class Done(TrainingEvent):
    pass


@dataclass(frozen=True, slots=True)
class Cancelled(TrainingEvent):
    pass


@dataclass(frozen=True, slots=True)
class Failed(TrainingEvent):
    details: str
