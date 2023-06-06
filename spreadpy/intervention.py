from . import Event
from . import SusceptibleToRecovered
import numpy as np
from . import VACCINE_STATES, MASKING_STATES

# TODO: #14 Simulator must initialize the required attributes 'masking', 'quarantine'

class Intervention(Event):
    ''' docstring '''

    def __init__(self, time, simulator, func=None, args=None):
        # TODO: #13 Rethink how interventions are defined in terms of args
        super().__init__(time, simulator)
        self.simulator = simulator
        self.func = func
        self.args = args

    def do(self):
        pass


class Masking(Intervention):
    '''docstring'''
    #MASKING_STATES = {'no masking': 0,
    #                  'masking': 1}

    def do(self):
        if self.simulator.verbose:
            print('Masking intervention')
        self.simulator.population['masking'] = self.func(self.args)
        self.simulator.population.update_transmission_weights()


class Quarantine(Intervention):
    '''docstring'''

    def __init__(self, time, simulator, idx, length=5):
        # TODO: #13 Rethink how interventions are defined in terms of args
        super().__init__(time, simulator)
        self.simulator = simulator
        self.idx = idx
        self.length = length

    def do(self):
        try:
            assert(len(self.simulator.population['quarantine']) ==
                   self.simulator.population.population_size)
        except AssertionError:
            self.simulator.population['quaratine'] = np.zeros(
                self.simulator.population.population_size)
        self.simulator.population['quarantine'][self.idx] = 1
        self.simulator.population.update_transmission_weights()
        EndQuarantine(self.simulator.now() + self.length, self.simulator,
                      self.idx)


class EndQuarantine(Intervention):

    def __init__(self, time, simulator, idx):
        # TODO: #13 Rethink how interventions are defined in terms of args
        super().__init__(time, simulator)
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population['quarantine'][self.idx] = 0
        self.simulator.population.update_transmission_weights()


class Vaccination(Intervention):
    '''docstring'''
    VACCINE_DELAY = 0
    VACCINE_STATES = {'not vaccinated': 0,
                      'vaccinated': 1}

    def __init__(self, time, simulator, disease_name,
                 target_func=None, **target_kwargs):
        super().__init__(time + Vaccination.VACCINE_DELAY, simulator)
        self.simulator = simulator
        self.disease_name = disease_name
        self.target_kwargs = target_kwargs
        self.target_func = target_func

    def do(self):
        # TODO: #8 Review how vaccination is applied based on coverage.
        if self.simulator.verbose:
            print('Vaccination intervention')
        target_idx = self.target_func(self.simulator.population,
                                      **self.target_kwargs)
        idx = np.where(
            (self.simulator.population[self.disease_name]['states'] ==
             self.simulator.population.diseases[
                 self.disease_name]['states']['susceptible']) &
            (self.simulator.population[self.disease_name]['vaccine'] == VACCINE_STATES[self.disease_name]['not vaccinated']))[0]

        target_idx = target_idx[np.isin(target_idx, idx, assume_unique=True)]
        self.simulator.population[
            self.disease_name]['vaccine'][target_idx] = VACCINE_STATES[self.disease_name]['vaccinated']
        SusceptibleToRecovered(self.simulator.now(), self.simulator,
                               self.simulator.population, target_idx)

def vaccinate_age(population, stream, age_target, coverage):
    idx_ = np.where((population['age'] >= age_target[0]) &
                    (population['age'] <= age_target[1]))[0]
    return stream.choice(idx_, size=round(int(len(idx_)*coverage)),
                         replace=False)