import sys
sys.path.append('../')
import numpy as np
from epydemia import Step

class DailyStep(Step):
    ''' Disease progression '''
    STEP_SIZE = 1 # Daily time step

    def __init__(self, time, simulator):
        super().__init__(time, simulator)

    @classmethod
    def initialize(cls, simulator):
        for t in np.arange(0, int(simulator.stop_time)+1, DailyStep.STEP_SIZE):
            DailyStep(t, simulator)

    def do(self):
        if self.simulator.verbose:
            print('New day beginning {}'.format(self.time))
        for _, disease in self.simulator.population.diseases.items():
            disease.infect()

        # Stats collections here
        for i, name in zip(range(4),
                           ['susceptible', 'exposed', 'infected', 'recovered']):
            stat = len(
                np.where(self.simulator.population['covid'] == i)[0])
            self.simulator.collector.collect(name, stat)
        self.simulator.collector.collect(
            'states', self.simulator.population['covid'].copy()
            )
        for label in ['masking', 'covid_vaccine']:
            try:
                self.simulator.collector.collect(
                    label, np.count_nonzero(self.simulator.population[label] == 1)
                )
            except:
                pass

