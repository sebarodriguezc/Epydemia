from . import Event, Simulator, Stream
from . import Population
from . import ImportCases
from . import Intervention, Masking, Vaccination, MaskingBehavior
from . import Disease, Covid
from . import StatsCollector
from . import from_file_proportion
import numpy as np
import random

class AgentBasedSim(Simulator):
    ''' docstring '''

    def __init__(self):
        super().__init__()
        self.population = None
        self.verbose = True

    def run(self, stop_time, verbose=True, seeds=(1024,)):
        self.verbose = verbose
        self.collector = StatsCollector()

        Covid.stream = Stream(seed=seeds[0])  # TODO: Assign streams for each disease class or object?

        Step.initialize(self, stop_time)
        super().run(stop_time)

    def initialize_population(self, how=None,
                              population_size=None,
                              avg_contacts_per_day=20,
                              network_seed=2048,
                              population_seed=3069,
                              pop_attributes=None,
                              filename=None,
                              **kwargs):
        '''
        '''
        # where to alocate avg_contacts_per_day population or sim.
        random.seed(network_seed)  # igraph seed
        self.stream = Stream(population_seed)
        if how == 'from_arrays':
            assert(isinstance(pop_attributes, dict))
            population_size = len(pop_attributes.items()[0][1])
            try:
                for key, val in pop_attributes.items():
                    assert(len(val) == population_size)
            except AssertionError:
                population_size = len(pop_attributes.items()[0][1])
            self.population = Population(population_size)
            for key, value in pop_attributes.items():
                self.population.add_attribute(key, value)
        elif how == 'proportion_file':
            assert(isinstance(filename, str))
            assert(isinstance(population_size, int))
            self.population = Population(population_size)
            pop_attributes, metadata = from_file_proportion(
                filename, population_size, self.stream)
            for key, value in pop_attributes.items():
                self.population.add_attribute(key, value)
        elif how == '':
            pass

    def add_intervention(self, InterventionCls, time, **intervention_kwargs):
        assert(issubclass(InterventionCls, Intervention))
        InterventionCls(time, self, **intervention_kwargs)

    def add_disease(self, DiseaseCls, *disease_args, **disease_kwargs):
        assert(issubclass(DiseaseCls, Disease))
        self.population.introduce_disease(DiseaseCls(self, *disease_args, **disease_kwargs))
        # ImportCases(0, self, [0, 2, 10, 15, 30])  # TODO: #12 implement how to import cases

    def add_layer(self, layer_name, **kwargs):
        ''' should be given the option to give the vertices' id to do a new layer'''
        if 'n' not in kwargs:
            kwargs['n'] = self.population.population_size
        self.population.network.add_layer(layer_name=layer_name, **kwargs)


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
        self.simulator.collector.collect(
            'masking', (self.simulator.population['masking'] == 1).sum())
        try:
            self.simulator.collector.collect(
                'sn', self.simulator.population['sn'].mean())
        except:
            pass

    @classmethod
    def initialize(cls, simulator, stop_time):
        for t in np.arange(0, int(stop_time)+1, Step.STEP_SIZE): 
            Step(t, simulator)
