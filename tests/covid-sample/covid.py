import sys
sys.path.append('../')
import numpy as np
from epydemia.simobjects import Disease
from epydemia.simevents import ChangeState
from epydemia.basedesim import Event

class SusceptibleToExposed(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'exposed')
        time = 0.5 + self.simulator.population.diseases['covid'].stream.weibull(4.6)
        ExposedToPresymptomatic(self.simulator.now() + time,
                                self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} got infected'.format(self.idx))


class SusceptibleToRecovered(ChangeState):

    def do(self):
        time = self.simulator.population.diseases['covid'].stream.gamma(25, 10)
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator,
                               self.idx)
        if self.simulator.verbose:
            print('Agent {} was immunized'.format(self.idx))


class ExposedToPresymptomatic(ChangeState):

    def do(self):
        time = 0.5
        self.simulator.population.change_state(self.idx, 'covid',
                                               'presymptomatic')
        if self.simulator.population.diseases['covid'].stream.random() < 1/3:
            PresymptomaticToSymptomatic(self.simulator.now() + time,
                                        self.simulator, self.idx)
        else:
            PresymptomaticToAsymptomatic(self.simulator.now() + time,
                                         self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} became presymptomatic'.format(self.idx))


class PresymptomaticToSymptomatic(ChangeState):

    def do(self):
        time = self.simulator.population.diseases['covid'].stream.exponential(3)
        self.simulator.population.change_state(self.idx, 'covid', 'symptomatic')
        if self.simulator.population.diseases['covid'].stream.random() < 0.03:
            SymptomaticToHospitalized(self.simulator.now() + time,
                                      self.simulator, self.idx)
        else:
            SymptomaticToRecovered(self.simulator.now() + time,
                                   self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} became symptomatic'.format(self.idx))

class SymptomaticToHospitalized(ChangeState):

    def do(self):
        time = self.simulator.population.diseases['covid'].stream.exponential(10.4)
        self.simulator.population.change_state(self.idx, 'covid', 'hospitalized')
        if self.simulator.population.diseases['covid'].stream.random() < 0.2:
            HospitalizedToDeath(self.simulator.now() + time,
                                self.simulator, self.idx)
        else:
            HospitalizedToRecovered(self.simulator.now() + time,
                                    self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} was hospitalized'.format(self.idx))

class HospitalizedToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} recovered from hospitalization'.format(self.idx))

class HospitalizedToDeath(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'death')
        # TODO: #16 cancel all events related to individual
        if self.simulator.verbose:
            print('Agent {} died from covid'.format(self.idx))

class PresymptomaticToAsymptomatic(ChangeState):

    def do(self):
        time =self.simulator.population.diseases['covid'].stream.exponential(2)
        self.simulator.population.change_state(self.idx, 'covid', 'asymptomatic')
        AsymptomaticToRecovered(self.simulator.now() + time,
                                self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} became asymptomatic'.format(self.idx))

class SymptomaticToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.gamma(25, 10)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} recovered from being symptomatic'.format(self.idx))

class AsymptomaticToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)
        if self.simulator.verbose:
            print('Agent {} recovered from being asymptomatic'.format(self.idx))

class RecoveredToSusceptible(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'susceptible')
        if self.simulator.verbose:
            print('Agent {} became susceptible'.format(self.idx))

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
        self.simulator.population.change_state(idx, 'covid', 'symptomatic')
        for person in idx:
            time = self.simulator.population.diseases['covid'].stream.exponential(5)
            SymptomaticToRecovered(self.simulator.now() + time,
                                   self.simulator, person)
            if self.simulator.verbose:
                print('Agent {} got infected outside of the network'.format(person))


class Covid(Disease):

    # TODO: #6 states could be a class attribute instead of object
    VACCINE_STATES = {
        'not vaccinated': 0,
        'vaccinated': 1}

    def __init__(self, simulator, stream, infection_prob=0.5,
                 initial_cases=5, vaccine_seed=None,
                 states={0: 'susceptible'}, **kwargs):
        super().__init__('covid', simulator, stream, infection_prob,
                         states=states, **kwargs)
        self['vaccine_seed'] = vaccine_seed
        self['initial_cases'] = initial_cases

    def initialize(self):
        if isinstance(self['vaccine_seed'], type(None)):
            self.population[self.name]['vaccine'] = np.full(
                self.population.size,
                Covid.VACCINE_STATES['not vaccinated'])
        else:
            assert(len(self['vaccine_seed']) == self.population.size)
            self.population[self.name]['states'] = self['vaccine_seed']
        ImportCases(0, self.simulator, self['initial_cases'])

    def infect(self):
        susceptibles, probability = \
            self.population.get_transmission_probabilities(
                'covid', susceptible_states=['susceptible'],
                infectee_states=[
                    'presymptomatic', 'symptomatic', 'asymptomatic'])
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
        vfunc = np.vectorize(masking_prob)
        masking_p = vfunc(*self.population['masking'][vertex_pair_seq].T)
        return masking_p*self['infection_prob']
