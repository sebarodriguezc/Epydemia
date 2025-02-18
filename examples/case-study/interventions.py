from epydemia import Intervention, vaccinate_age
from covid import SusceptibleToRecovered
import numpy as np

class RandomMasking(Intervention):
    '''docstring'''

    def do(self):
        if self.simulator.verbose:
            print('Masking intervention')
        n = self.simulator.population.size
        p = self.kwargs['coverage']
        self.simulator.population['masking'] = np.random.choice([0, 1],
                                                                size=(n,),
                                                                p=[1-p, p])
        self.simulator.population.update_transmission_probabilities()
        if self.simulator.verbose:
            print('Face mask usage at {}%'.format(int(p*100)))


class Vaccination(Intervention):
    '''docstring'''

    def __init__(self, time, simulator,
                 age_target, coverage):
        super().__init__(time, simulator)
        self.age_target = age_target
        self.coverage = coverage

    def do(self):
        # TODO: #8 Implement function to randomly mask people in a certain age group. Vaccinated 0 or 1.
        if self.simulator.verbose:
            print('Vaccination intervention')

        target_idx = vaccinate_age(self.simulator.population, self.simulator.streams['vaccination'], self.age_target, self.coverage)
        idx = np.where(
            (self.simulator.population['covid'] ==
             self.simulator.population.diseases[
                 'covid']['states']['susceptible']) &
            (self.simulator.population[
                'covid_vaccine'] == 0))[0]

        target_idx = target_idx[np.isin(target_idx, idx, assume_unique=True)]
        
        self.simulator.population[
                'covid_vaccine'][target_idx] = 1

        SusceptibleToRecovered(self.simulator.now(),
                               self.simulator, target_idx)