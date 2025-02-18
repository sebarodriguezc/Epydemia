from typing import Union
from epydemia import ChangeState, Event, AbstractDisease, Intervention, Simulator
import numpy as np

class SusceptibleToExposed(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'exposed')
        time = 0.5 + self.simulator.population.diseases['covid'].stream.exponential(10)
        ExposedToInfected(self.simulator.now() + time,
                                self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} became infected'.format(self.idx))

class SusceptibleToRecovered(ChangeState):

    def do(self):
        time = self.simulator.population.diseases['covid'].stream.gamma(25, 10)
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        if self.simulator.verbose:
            print('Agent {} got vaccinated'.format(self.idx))

class ExposedToInfected(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid',
                                               'infected')
        time = self.simulator.population.diseases['covid'].stream.exponential(7)
        InfectedToRecovered(self.simulator.now() + time,
                                        self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} became exposed'.format(self.idx))

        if 'quarantine' in self.simulator.population.attributes.keys():
            if self.simulator.streams['quarantine'].uniform() <= self.simulator.population['prob_quarantine']:
                BeginQuarantine(self.simulator.now(), self.simulator, idx = self.idx,
                                duration = self.simulator.population['quarantine_duration'])


class InfectedToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        if self.simulator.verbose:
            print('Agent {} got recovered'.format(self.idx))

class ImportCases(Event):

    def __init__(self, time, simulator, cases=1):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.cases = cases

    def do(self):
        susceptibles = self.simulator.population.get_state(
            'covid', 'susceptible')
        idx = self.simulator.population.diseases['covid'].stream.choice(
            susceptibles, size=self.cases, replace=False)
        self.simulator.population.change_state(idx, 'covid', 'infected')
        for person in idx:
            time = self.simulator.population.diseases['covid'].stream.exponential(5)
            InfectedToRecovered(self.simulator.now() + time,
                                   self.simulator, person)
            if self.simulator.verbose:
                print('Agent {} is an imported case'.format(person))
            
class Covid(AbstractDisease):

    def __init__(self, simulator, infection_prob,
                 initial_cases, states, **attributes):
        super().__init__('covid', simulator, infection_prob,
                         states, **attributes)
        self['initial_cases'] = initial_cases

    def initialize(self):
        ImportCases(0, self.simulator, self['initial_cases'])

    def infect(self):
        susceptibles, probability = self.population.get_transmission_probabilities(
            'covid', ['susceptible'], ['infected'])
        exposed = susceptibles[np.where(
            self.stream.random(len(probability)) <= probability)]
        for person in exposed:
            SusceptibleToExposed(self.simulator.now(),
                                 self.simulator, person)

    def compute_transmission_probabilities(self, vertex_pair_seq):
        '''
        Update transmission must consider all interventions
        '''
        # TODO: #1 determine which factors affect transmission (masking, quarantine, vaccination)
        def masking_prob(i, j):
            if i+j == 0:
                return 1
            elif i+j == 1:
                return 0.5
            else:
                return 0.3
        def quarantine_prob(i, j):
            if i+j == 0:
                return 1
            else:
                return 0
        try:
            masking_p = np.array([masking_prob(i,j) for i,j in self.population['masking'][vertex_pair_seq]])
        except:
            masking_p = np.ones(len(vertex_pair_seq))
        try:
            quarantine_p = np.array([quarantine_prob(i,j) for i,j in self.population['quarantine'][vertex_pair_seq]])
        except:
            quarantine_p = np.ones(len(vertex_pair_seq))
        return masking_p*quarantine_p*self['infection_prob']

class BeginQuarantine(Event):
    
    def __init__(self, time: int | float, simulator: Simulator,
                 idx, duration):
        super().__init__(time, simulator)
        self.idx = idx
        self.duration = duration

    def do(self):
        if self.simulator.verbose:
            print('Agent {} began quarantine'.format(self.idx))
        
        self.simulator.population['quarantine'][self.idx] = 1
        self.simulator.population.update_transmission_probabilities(target_vertex_seq=[self.idx])
        EndQuarantine(self.simulator.now() + self.duration, self.simulator, idx=self.idx)
        self.simulator.collector.collect('quarantine', (self.simulator.now(), 1))

class EndQuarantine(Event):
    '''docstring'''

    def __init__(self, time: int | float, simulator: Simulator,
                 idx):
        super().__init__(time, simulator)
        self.idx = idx

    def do(self):
        if self.simulator.verbose:
            print('Agent {} ended quarantine'.format(self.idx))
        
        self.simulator.population['quarantine'][self.idx] = 0
        self.simulator.population.update_transmission_probabilities(target_vertex_seq=[self.idx])
        self.simulator.collector.collect('quarantine', (self.simulator.now(), -1))
