from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models import Job
from app.run import ExecutionContext


@dataclass(frozen=True, kw_only=True, slots=True)
class TrainerContext(ExecutionContext[Job]):
    pass


class Trainer(ABC):
    @abstractmethod
    def run(self, ctx: TrainerContext) -> None: ...
