from . import Event, Simulator, Stream
from . import Population
from . import ImportCases
from . import Masking, Vaccination
from . import Covid
from . import StatsCollector
import numpy as np
import random

class AgentBasedSim(Simulator):
    ''' docstring '''

    def __init__(self, events=None):
        super().__init__(events)
        self.population = None
        self.verbose = True
        self.S, self.E, self.I, self.R, self.H, self.D = [], [], [], [], [], []

    def run(self, stop_time, verbose=True, seeds=(1024,)):
        self.verbose = verbose
        self.collector = StatsCollector()
        disease_stream = Stream(seed=seeds[0])
        Covid.stream = disease_stream
        Step.initialize(self, stop_time)
        super().run(stop_time)

    def initialize_population(self, population_size=100, avg_contacts_per_day=20,
                   network_seed=2048, **kwargs):
        # where to alocate avg_contacts_per_day population or sim.
        random.seed(network_seed)  # igraph seed
        self.population = Population(population_size, **kwargs)
        ImportCases(0, self, self.population, [0, 2, 10, 15, 30])

    def add_intervention(self, intervention_type, time, **intervention_kwargs):
        # TODO: #5 can have a list of interventions instead of if statements
        if intervention_type == 'Masking':
            Masking(time, self, **intervention_kwargs)
        elif intervention_type == 'Vaccination':
            Vaccination(time, self, **intervention_kwargs)

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
        for _, disease in self.simulator.population.diseases.items():
            disease.progression(self.simulator.population)
            # Stats collections here
        for i, name in zip(range(8), ['S', 'E', 'P', 'Sy', 'A', 'R', 'H', 'D']):
            stat = len(np.where(self.simulator.population['covid']['states'] == i)[0])
            self.simulator.collector.collect(name, stat)

    @classmethod
    def initialize(cls, simulator, stop_time):
        for t in np.arange(0, int(stop_time)+1, Step.STEP_SIZE):    ## add the below to a initialize function ?????
            Step(t, simulator)
