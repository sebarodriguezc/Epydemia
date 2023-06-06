from . import SelfObject, Event, Stream
import numpy as np
from abc import ABC, abstractmethod

class Disease(SelfObject, ABC):
    ''' docstring '''

    def __init__(self, name, attributes):
        # states
        self.name = name
        super().__init__(attributes)

    @abstractmethod
    def progression(self):
        pass

    def update_transmission(self, population, edge_seq, vertex_seq):
        pass


'''
class ChangeState(Event):

    def __init__(self, time, simulator, population_ids, disease_name, to_state):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = population_ids
        self.to_state = to_state
        self.disease_name = disease_name

    def do(self):
        self.simulator.population[self.disease_name]['states'][self.idx] = self.to_state
        print('Changing state to ', self.to_state)
'''


class SusceptibleToExposed(Event):

    # TODO: This EVENT might need to change to accept idx and code do() outside.

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'exposed')
        time = 0.5 + Covid.stream.weibull(4.6)
        ExposedToPresymptomatic(self.simulator.now() + time,
                                self.simulator, self.idx)


class SusceptibleToRecovered(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        time = Covid.stream.gamma(25, 10)
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator,
                               self.idx)


class ExposedToPresymptomatic(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        time = 0.5
        self.simulator.population.change_state(self.idx, 'covid', 'presymptomatic')
        if Covid.stream.random() < 1/3:
            PresymptomaticToSymptomatic(self.simulator.now() + time,
                                        self.simulator, self.idx)
        else:
            PresymptomaticToAsymptomatic(self.simulator.now() + time,
                                         self.simulator, self.idx)


class PresymptomaticToSymptomatic(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        time = Covid.stream.exponential(3)
        self.simulator.population.change_state(self.idx, 'covid', 'symptomatic')
        if Covid.stream.random() < 0.03:
            SymptomaticToHospitalized(self.simulator.now() + time,
                                      self.simulator, self.idx)
        else:
            SymptomaticToRecovered(self.simulator.now() + time,
                                   self.simulator, self.idx)


class SymptomaticToHospitalized(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        time = Covid.stream.exponential(10.4)
        self.simulator.population.change_state(self.idx, 'covid', 'hospitalized')
        if Covid.stream.random() < 0.2:
            HospitalizedToDeath(self.simulator.now() + time,
                                self.simulator, self.idx)
        else:
            HospitalizedToRecovered(self.simulator.now() + time,
                                    self.simulator, self.idx)


class HospitalizedToRecovered(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = Covid.stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class HospitalizedToDeath(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'death')
        # TODO: #16 cancel all events related to individual


class PresymptomaticToAsymptomatic(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        time = Covid.stream.exponential(2)
        self.simulator.population.change_state(self.idx, 'covid', 'asymptomatic')
        AsymptomaticToRecovered(self.simulator.now() + time,
                                self.simulator, self.idx)


class SymptomaticToRecovered(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = Covid.stream.gamma(25, 10)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class AsymptomaticToRecovered(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'recovered')
        time = Covid.stream.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time,
                               self.simulator, self.idx)


class RecoveredToSusceptible(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'susceptible')


class ImportCases(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx

    def do(self):
        self.simulator.population.change_state(self.idx, 'covid', 'symptomatic')
        for person in self.idx:
            time = Covid.stream.exponential(5)
            SymptomaticToRecovered(self.simulator.now() + time,
                                   self.simulator, person)


class Covid(Disease):

    stream = Stream(seed=1)
    # TODO: #6 states could be a class attribute instead of object

    def __init__(self, simulator, attributes):
        super().__init__('covid', attributes)
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
        self['infection_prob'] = attributes['infection_prob']
        self.simulator = simulator

    def progression(self, population):
        susceptibles, probability = population.get_suceptible_prob(
            'covid')
        exposed = susceptibles[np.where(
            Covid.stream.random(len(probability)) <= probability)]
        for person in exposed:
            SusceptibleToExposed(self.simulator.now(),
                                 self.simulator, person)

    def update_transmission(self, population, edge_seq, vertex_seq):
        '''
        Update transmission considers all interventions ?
        '''
        # TODO: #1 determine which factors affect transmission (masking, quarantine, vaccination)
        def masking_prob(i, j):
            if i+j == 0:
                return 1
            elif i+j == 1:
                return 0.75
            else:
                return 0.2
        vfunc = np.vectorize(masking_prob)
        masking_p = vfunc(*population['masking'][vertex_seq].T)
        return masking_p*self['infection_prob']
