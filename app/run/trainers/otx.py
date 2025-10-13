from app.runnables.trainers import Trainer, TrainerContext


class OTXTrainer(Trainer):
    def run(self, ctx: TrainerContext) -> None:
        raise NotImplementedError
