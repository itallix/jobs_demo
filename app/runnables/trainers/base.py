from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.runnables.base import ExecutionContext


@dataclass(frozen=True, kw_only=True, slots=True)
class TrainerContext(ExecutionContext):
    pass


class Trainer(ABC):
    @abstractmethod
    def run(self, ctx: TrainerContext) -> None: ...
