from base import SelfObject
from base import Event
import numpy as np

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

class Disease(SelfObject):
    ''' docstring '''

    def __init__(self, name, attributes):
        # states
        self.name = name
        super().__init__(attributes)

    def progression(self):
        pass


class SusceptibleToExposed(Event):

    def __init__(self, time, simulator, population):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population

    def do(self):
        susceptibles, probability = self.population.get_suceptible_prob('covid')
        exposed = susceptibles[np.where(
            np.random.random(len(probability)) <= probability)]
        self.population.change_state(exposed, 'covid', 'exposed')
        for person in exposed:
            time = 0.5 + np.random.weibull(4.6)
            ExposedToPresymptomatic(self.simulator.now() + time, self.simulator, self.population, person)


class ExposedToPresymptomatic(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        time = 0.5
        self.population.change_state(self.idx, 'covid', 'presymptomatic')
        if np.random.random() < 1/3:
            PresymptomaticToSymptomatic(self.simulator.now() + time, self.simulator, self.population, self.idx)
        else:
            PresymptomaticToAsymptomatic(self.simulator.now() + time, self.simulator, self.population, self.idx)


class PresymptomaticToSymptomatic(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        time = np.random.exponential(3)
        self.population.change_state(self.idx, 'covid', 'symptomatic')
        if np.random.random() < 0.03:
            SymptomaticToHospitalized(self.simulator.now() + time, self.simulator, self.population, self.idx)
        else:
            SymptomaticToRecovered(self.simulator.now() + time, self.simulator, self.population, self.idx)


class SymptomaticToHospitalized(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        time = np.random.exponential(10.4)
        self.population.change_state(self.idx, 'covid', 'hospitalized')
        if np.random.random() < 0.2:
            HospitalizedToDeath(self.simulator.now() + time, self.simulator, self.population, self.idx)
        else:
            HospitalizedToRecovered(self.simulator.now() + time, self.simulator, self.population, self.idx)

class HospitalizedToRecovered(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'recovered')
        time = np.random.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator, self.population, self.idx)


class HospitalizedToDeath(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'death')


class PresymptomaticToAsymptomatic(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        time = np.random.exponential(2)
        self.population.change_state(self.idx, 'covid', 'asymptomatic')
        AsymptomaticToRecovered(self.simulator.now() + time, self.simulator, self.population, self.idx)


class SymptomaticToRecovered(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'recovered')
        time = np.random.gamma(25, 10)
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator, self.population, self.idx)


class AsymptomaticToRecovered(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'recovered')
        time = np.random.exponential(20)
        RecoveredToSusceptible(self.simulator.now() + time, self.simulator, self.population, self.idx)

class RecoveredToSusceptible(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'susceptible')


class ImportCases(Event):

    def __init__(self, time, simulator, population, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.population = population
        self.idx = idx

    def do(self):
        self.population.change_state(self.idx, 'covid', 'symptomatic')
        for person in self.idx:
            time = np.random.exponential(5)
            SymptomaticToRecovered(self.simulator.now() + time, self.simulator, self.population, person)


class Covid(Disease):

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
        SusceptibleToExposed(self.simulator.now(), self.simulator, population)