from . import Event
from . import Step
import numpy as np


class SampleDailyStep(Step):

    STEP_SIZE = 1

    def __init__(self, time, simulator):
        super().__init__(time, simulator)

    @classmethod
    def initialize(cls, simulator):
        for t in np.arange(0, int(simulator.stop_time)+1,
                           SampleDailyStep.STEP_SIZE):
            SampleDailyStep(t, simulator)

    def do(self):
        for _, disease in self.simulator.population.diseases.items():
            disease.infect(self.simulator.population)


class ChangeState(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.idx = idx

    def do(self):
        pass