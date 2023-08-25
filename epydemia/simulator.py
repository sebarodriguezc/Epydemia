from . import Event, Simulator, Stream
from . import Population
from . import Intervention
from . import Disease
from . import StatsCollector
from . import from_file_proportion
import random

class AgentBasedSim(Simulator):
    ''' docstring '''

    def __init__(self, StepCls):
        super().__init__()
        self.population = None
        self.collector = None
        self.verbose = True
        assert(issubclass(StepCls, Step))
        self.step = StepCls

    def run(self, stop_time, verbose=True, seeds=(1024,)):
        self.verbose = verbose
        self.collector = StatsCollector()
        self.stop_time = stop_time

        #Covid.stream = Stream(seed=seeds[0])  # TODO: Assign streams for each disease class or object?

        self.step.initialize(self)
        super().run(self.stop_time)

    def create_population(self, how='basic',
                              population_size=None,
                              network_seed=2048,
                              population_seed=3069,
                              pop_attributes=None,
                              filename=None,
                              **kwargs):
        '''
        '''
        # where to alocate avg_contacts_per_day population or sim.
        random.seed(network_seed)  # igraph seed
        stream = Stream(population_seed)
        if how == 'basic':
            self.population = Population(population_size)
        elif how == 'from_arrays':
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
                filename, population_size, stream)
            for key, value in pop_attributes.items():
                self.population.add_attribute(key, value)
        else:
            raise NotImplementedError('Method not implemented')
        
    def add_intervention(self, InterventionCls, time, **intervention_kwargs):
        assert(issubclass(InterventionCls, Intervention))
        InterventionCls(time, self, **intervention_kwargs)

    def add_disease(self, DiseaseCls, states_seed=None,
                    disease_kwargs={}):
        try:
            assert(not isinstance(self.population, type(None)))
        except AssertionError:
            raise ValueError('Population not found. A population must be initialize first.')
        assert(issubclass(DiseaseCls, Disease))
        self.population.introduce_disease(
            DiseaseCls(self, **disease_kwargs),
            states_seed)
        # ImportCases(0, self, [0, 2, 10, 15, 30])  # TODO: #12 implement how to import cases

    def add_layer(self, layer_name, **kwargs):
        ''' should be given the option to give the vertices' id to do a new layer'''
        if 'n' not in kwargs:
            kwargs['n'] = self.population.size
        self.population.network.add_layer(layer_name=layer_name, **kwargs)


class Step(Event):

    def __init__(self, time, simulator):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator

    def do(self):
        pass
    
    @classmethod
    def initialize(cls, simulator, *args, **kwargs):
        pass
