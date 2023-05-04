from base import SelfObject, Event, Simulator
import numpy as np
from disease import ChangeState

class AgentBasedSim(Simulator):
    ''' docstring '''

    def __init__(self, step, events=None):
        if issubclass(step, Event):
            self.step = step
        else:
            raise TypeError  # type error
        super().__init__(events)
        self.population = None
        self.verbose = True
        self.S, self.E, self.I, self.R, self.H, self.D = [], [], [], [], [], []

    def set_population(self, population):
        self.population = population

    def run(self, stop_time, step_length, verbose=True):
        self.verbose = verbose
        ## add the below to a initialize function ?????
        for t in range(int(stop_time)+1):
            self.step(t, self, step_length)
        super().run(stop_time)


class Step(Event):
    ''' Disease progression '''

    def __init__(self, time, simulator, step_length):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.step_size = step_length

    def do(self):
        if self.simulator.verbose:
            print('New day beginning {}'.format(self.time))
        for disease_name, disease in self.simulator.population.diseases.items():
            disease.progression(self.simulator.population)
        if self.simulator.verbose:
            susceptible = len(np.where(self.simulator.population['covid']['states'] == 0)[0])
            recovered = len(np.where(self.simulator.population['covid']['states'] == 5)[0])
            infected = len(np.where(self.simulator.population['covid']['states'] == 2)[0])
            exposed = len(np.where(self.simulator.population['covid']['states'] == 1)[0])
            hosp = len(np.where(self.simulator.population['covid']['states'] == 6)[0])
            death = len(np.where(self.simulator.population['covid']['states'] == 7)[0])
            self.simulator.S.append(susceptible)
            self.simulator.E.append(exposed)
            self.simulator.I.append(infected)
            self.simulator.R.append(recovered)
            self.simulator.H.append(hosp)
            self.simulator.D.append(death)


class Intervention(Event):
    ''' docstring '''

    def __init__(self, time, simulator, func, args):
        super().__init__(time, simulator)
        self.model = simulator
        self.func = func
        self.args = args

    def do(self):
        pass
