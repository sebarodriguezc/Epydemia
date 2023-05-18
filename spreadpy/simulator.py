from . import Event, Simulator, Stream
from . import Population
from . import ImportCases
from . import Masking
from . import Covid
import numpy as np
import random

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

    def run(self, stop_time, verbose=True, seeds=(1024, 2048)):
        self.verbose = verbose
        disease_stream = Stream(seed=seeds[0])
        Covid.stream = disease_stream
        random.seed(seeds[1])

        for t in np.arange(0, int(stop_time)+1, Step.STEP_SIZE):    ## add the below to a initialize function ?????
            self.step(t, self)
        super().run(stop_time)

    def initialize(self, population_size=100, avg_contacts_per_day=20):
            self.population = Population(population_size)
            # pop.create_random_contact_layer(p=0.02, layer_name='schools')
            # pop.create_random_contact_layer(p=0.05, layer_name='workplaces')
            ImportCases(0, self, self.population, [0, 2, 10, 15, 30])

    def add_intervention(self, intervention_type, time, **intervention_kwargs):
        if intervention_type == 'Masking':
            Masking(time, self, **intervention_kwargs)

    def add_disease(self, disease_type, *disease_args, **disease_kwargs):
        if disease_type == 'covid':
            disease = Covid(self, *disease_args, **disease_kwargs)
        self.population.introduce_disease(disease)

    def add_layer(self, how='random', **kwargs):
        if how == 'random':
            self.population.create_random_contact_layer(**kwargs)



class Step(Event):
    ''' Disease progression '''
    STEP_SIZE = 1 # Daily time step

    def __init__(self, time, simulator):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator

    def do(self):
        if self.simulator.verbose:
            print('New day beginning {}'.format(self.time))
        for disease_name, disease in self.simulator.population.diseases.items():
            disease.progression(self.simulator.population)
            ## Stats collections here
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