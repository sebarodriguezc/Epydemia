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

    def run(self, stop_time, verbose=True, seeds=(1024,)):
        self.verbose = verbose
        self.collector = StatsCollector()
        disease_stream = Stream(seed=seeds[0])
        Covid.stream = disease_stream
        Step.initialize(self, stop_time)
        super().run(stop_time)

    def initialize_population(self, population_size=100,
                              avg_contacts_per_day=20,
                              network_seed=2048,
                              pop_attributes=None,
                              filename=None,
                              **kwargs):
        # where to alocate avg_contacts_per_day population or sim.
        random.seed(network_seed)  # igraph seed
        if not isinstance(filename, type(None)):
            pass  # TODO: #11 implement reading from file
        else:
            self.population = Population(population_size)
            if isinstance(pop_attributes, dict):
                for key, value in pop_attributes.items():
                    self.population.add_attribute(key, value)
        ImportCases(0, self, self.population, [0, 2, 10, 15, 30])  # TODO: #12 implement how to import cases

    def add_intervention(self, intervention_type, time, **intervention_kwargs):
        # TODO: #5 can have a list of interventions instead of if statements
        if intervention_type == 'masking':
            Masking(time, self, **intervention_kwargs)
        elif intervention_type == 'vaccination':
            Vaccination(time, self, **intervention_kwargs)

    def add_disease(self, disease_type, *disease_args, **disease_kwargs):
        if disease_type == 'covid':
            disease = Covid(self, *disease_args, **disease_kwargs)
        self.population.introduce_disease(disease)

    def add_layer(self, layer_name, how='random', **kwargs):
        ''' should be given the option to give the vertices' id to do a new layer'''
        if 'n' not in kwargs:
            kwargs['n'] = self.population.population_size
        if how == 'random':
            self.population.network.add_layer(layer_name=layer_name, how=how, **kwargs)
            

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
        for i, name in zip(range(8),
                           ['S', 'E', 'P', 'Sy', 'A', 'R', 'H', 'D']):
            stat = len(
                np.where(self.simulator.population['covid']['states'] == i)[0])
            self.simulator.collector.collect(name, stat)

    @classmethod
    def initialize(cls, simulator, stop_time):
        for t in np.arange(0, int(stop_time)+1, Step.STEP_SIZE):    # add the below to a initialize function ?????
            Step(t, simulator)
