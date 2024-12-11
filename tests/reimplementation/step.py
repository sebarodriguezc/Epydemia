import sys
sys.path.append('../')
import numpy as np
from epydemia import Step

class DailyStep(Step):
    ''' Disease progression '''
    STEP_SIZE = 1 # Daily time step

    def __init__(self, simulator, time):
        super().__init__(simulator, time)

    @classmethod
    def initialize(cls, simulator):
        for t in np.arange(0, int(simulator.stop_time)+1, DailyStep.STEP_SIZE):
            DailyStep(simulator, t)

    def do(self):
        if self.simulator.verbose:
            print('New day beginning {}'.format(self.time))
        for _, disease in self.simulator.population.diseases.items():
            disease.infect()

        # Stats collections here
        for i, name in zip(range(8),
                           ['S', 'E', 'P', 'Sy', 'A', 'R', 'H', 'D']):
            stat = len(
                np.where(self.simulator.population['covid'] == i)[0])
            self.simulator.collector.collect(name, stat)
        self.simulator.collector.collect(
            'masking', (self.simulator.population['masking'] == 1).sum())
        self.simulator.collector.collect(
            'states', self.simulator.population['covid'].copy()
            )
        try:
            self.simulator.collector.collect(
                'sn', self.simulator.population['sn'].mean())
        except:
            pass
