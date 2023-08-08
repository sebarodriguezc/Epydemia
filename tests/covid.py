import sys
sys.path.append('../')
import numpy as np
from spreadpy.disease import Disease
from spreadpy.special_events import ChangeState
from spreadpy.basedesim import Event

class SusceptibleToExposed(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'exposed')
        time = 0.5 + self.simulator.population.diseases['covid'].stream.weibull(4.6)
        ExposedToPresymptomatic(self.simulator.now() + time,
                                self.simulator, self.idx)


class SusceptibleToRecovered(ChangeState):

    def do(self):
        time = self.simulator.population.diseases['covid'].stream.gamma(25, 10)
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator,
                               self.idx)


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


class HospitalizedToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class HospitalizedToDeath(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'death')
        # TODO: #16 cancel all events related to individual


class PresymptomaticToAsymptomatic(ChangeState):

    def do(self):
        time =self.simulator.population.diseases['covid'].stream.exponential(2)
        self.simulator.population.change_state(self.idx, 'covid', 'asymptomatic')
        AsymptomaticToRecovered(self.simulator.now() + time,
                                self.simulator, self.idx)


class SymptomaticToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.gamma(25, 10)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class AsymptomaticToRecovered(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = self.simulator.population.diseases['covid'].stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class RecoveredToSusceptible(ChangeState):

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'susceptible')


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


class Covid(Disease):

    # TODO: #6 states could be a class attribute instead of object
    VACCINE_STATES = {
        'not vaccinated': 0,
        'vaccinated': 1}

    def __init__(self, simulator, stream, infection_prob=0.5,
                 initial_cases=5, vaccine_seed=None, **kwargs):
        super().__init__('covid', simulator, stream, infection_prob, **kwargs)
        self['states'] = {'susceptible': 0,
                          'exposed': 1,
                          'presymptomatic': 2,
                          'symptomatic': 3,
                          'asymptomatic': 4,
                          'recovered': 5,
                          'hospitalized': 6,
                          'death': 7}
        self['contagious_states'] = [self['states']['presymptomatic'],
                                     self['states']['symptomatic'],
                                     self['states']['asymptomatic']]
        self['infection_prob'] = infection_prob
        self['vaccine_seed'] = vaccine_seed
        ImportCases(0, self.simulator, initial_cases)  # TODO: #12 implement how to import cases

    def initialize(self, population):
        if isinstance(self['vaccine_seed'], type(None)):
            population[self.name]['vaccine'] = np.full(
                population.size,
                Covid.VACCINE_STATES['not vaccinated'])
        else:
            assert(len(self['vaccine_seed']) == population.size)
            population[self.name]['states'] = self['vaccine_seed']

    def progression(self, population):
        susceptibles, probability = population.get_suceptible_prob(
            'covid')
        exposed = susceptibles[np.where(
            self.stream.random(len(probability)) <= probability)]
        for person in exposed:
            SusceptibleToExposed(self.simulator.now(),
                                 self.simulator, person)

    def update_transmission(self, population, edge_seq, vertex_seq):
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
        masking_p = vfunc(*population['masking'][vertex_seq].T)
        return masking_p*self['infection_prob']
