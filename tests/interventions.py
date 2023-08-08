import sys
sys.path.append('../')
import numpy as np
from spreadpy.intervention import Intervention
from spreadpy.parameters import MASKING_STATES, VACCINE_STATES
from covid import SusceptibleToRecovered
import time

class Masking(Intervention):
    '''docstring'''

    def do(self):
        if self.simulator.verbose:
            print('Masking intervention')
        self.simulator.population['masking'] = self.kwargs[
            'func'](self.kwargs['args'])
        self.simulator.population.update_transmission_weights()


class MaskingBehavior(Intervention):
    '''docstring'''

    def __init__(self, time, simulator, stream):
        super().__init__(time, simulator)
        self.simulator = simulator
        self.stream = stream

    def do(self):
        def proportion_masked(population, x):
            return (population['masking'][x] == MASKING_STATES[
                'masking']).sum()/len(x)

        def neighbors_are_symptomatic(population, x):
            if any(population['covid']['states'][x] == population.diseases[
                    'covid']['states']['symptomatic']):
                return 1
            else:
                return 0

        def proportion_neighbors_symptomatic(population, x):
            return np.isin(population['covid']['states'][x],
                           population.diseases['covid']['states'][
                               'symptomatic']).sum()/len(x)

        def hospitalized_deaths(population, x):
            if any(population['covid']['states'][x] == population.diseases[
                    'covid']['states']['hospitalized']) or any(
                population['covid'][
                    'states'][x] == population.diseases['covid'][
                        'states']['hospitalized']):
                return 1
            else:
                return 0

        def total_hospitalized(population):
            if any(population[
                'covid']['states'] == population.diseases[
                    'covid']['states']['hospitalized']):
                return np.ones(population.size)
            else:
                return np.zeros(population.size)
        if self.simulator.verbose:
            print('Masking behavior')

        pop = self.simulator.population
        base_prob = 0
        neighbors = pop.network.get_neighbors()
        pop['sn'] = np.array(list(map(
            proportion_masked,
            list(pop for n in neighbors),
            neighbors)))
        pop['susceptibility'] = np.array(list(map(
            neighbors_are_symptomatic,
            list(pop for n in neighbors),
            neighbors)))
        #pop['susceptibility'] = np.array(list(map(
        #    proportion_neighbors_symptomatic,
        #    list(pop for n in neighbors),
        #    neighbors)))
        # TODO: #20 vectorize the above
        # pop['severity'] = np.array(list(map(hospitalized_deaths,
        #                                    neighbors)))
        #pop['severity'] = total_hospitalized(pop)
        pop['severity'] = np.array(list(map(
            hospitalized_deaths,
            list(pop for n in neighbors),
            neighbors)))
        bi = pop['w1']*pop['susceptibility'] + pop['w2']*pop['severity'] + pop[
            'w3']*pop['sn'] + pop['w4']*pop['pbc']
        p_bi = 1/(1 + np.exp(-12*(bi - 0.2)))*(1-base_prob) + base_prob 
        pop['masking'] = np.where(
            self.stream.rand(pop.size) < p_bi,
            MASKING_STATES['masking'],
            MASKING_STATES['no masking'])
        pop['pbc'] = np.where(
            pop['masking'] == MASKING_STATES['masking'],
            pop['pbc'] + (1 - pop['pbc'])*0.1,
            pop['pbc'] - (1 - pop['pbc'])*0.1)
        pop.update_transmission_weights()


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
                   self.simulator.population.size)
        except AssertionError:
            self.simulator.population['quaratine'] = np.zeros(
                self.simulator.population.size)
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
        SusceptibleToRecovered(self.simulator.now(),
                               self.simulator, target_idx)
