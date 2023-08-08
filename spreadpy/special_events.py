from . import Event
import numpy as np

class Step(Event):

    def __init__(self, time, simulator):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator

    def do(self):
        pass
    
    @classmethod
    def initialize(cls, simulator, *args, **kwargs):
        pass

class SampleDailyStep(Step):

    STEP_SIZE = 1

    def __init__(self, time, simulator):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator

    @classmethod
    def initialize(cls, simulator):
        for t in np.arange(0, int(simulator.stop_time)+1, SampleDailyStep.STEP_SIZE):
            SampleDailyStep(t, simulator)

    def do(self):
        for _, disease in self.simulator.population.diseases.items():
            disease.progression(self.simulator.population)

class ChangeState(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        pass