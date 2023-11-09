from . import Simulator, Stream
from . import Population, StatsCollector
from . import AbstractDisease
from . import Intervention, Step
from . import from_file_proportion
import random
import numpy as np
import pandas as pd
from typing import Type, Union, List


class AgentBasedSim(Simulator):
    """ Main simulation class. A AgentBasedSim object is used to handle
    all events (interventions) and run a simulation. It is also used to
    access objects across the simulation (i.e. population).

    It requires a Step class and a Population to run. The step class defines
    a step function that checks for new infected (daily step, continuous step,
    etc). The Step can also be used to update statistics (otherwise an
    intervention can be designed for this purpose).
    """

    def __init__(self, StepCls: Type[Step]):
        """ The initialization of a simulator object requires a Step class.
        When creating an object, the following attributes are defined:
        - population: Population object with agents' information.
        - collector: A statistics collector object.
        - verbose: Parameter used to activate output printing.
        - step: The user defined step class.

        Args:
            StepCls (Step class): Step class defined for the simulation.
        """
        super().__init__()
        self.population = None
        self.collector = None
        self.verbose = True
        assert(issubclass(StepCls, Step))
        self.step = StepCls
        self.streams = dict()
        self.stop_time = None

    def run(self, stop_time: Union[float, int],
            seeds: dict,
            verbose: bool = True):
        """ Method called to run the simulation. It can be override by
        the user to implement additional operations.

        Args:
            stop_time (float): time until simulation is run. If an infinity
                                value is given, the simulation will run until
                                no more events are scheduled.
            verbose (bool, optional): parameter used to activate the printing
                                      across the simulation. Defaults to True.
            seeds (tuple, optional): _description_. Defaults to (1024,).
        """
        self.verbose = verbose
        self.collector = StatsCollector()
        self.stop_time = stop_time
        
        # Setup diseases
        try:
            for disease_label, disease in self.population.diseases.items():
                disease.set_stream(Stream(seeds.pop(disease_label)))
                disease.initialize()
        except:
            raise ValueError('A random seed for each disease must be given.')

        #Setup rest of streams
        for key, seed in seeds.items():
            self.streams[key] = Stream(seed)

        # Initialize network
        self.population.network.initialize()

        # Schedule interventions

        # Initialize main step
        self.step.initialize(self)
        
        # Run model
        super().run(self.stop_time)

    def create_population(self, how: str = 'basic',
                          population_size: int = None,
                          population_random_seed: int = 3069,
                          network_random_seed: int = 2048,
                          pop_attributes: dict = dict(),
                          filename: str = None, **network_kwargs):
        """ Method used to create a population. There are several ways
        on building one:
        - 'basic': creates a Population object of a desired size.
        - 'from_arrays': using a dictionary with arrays that define
                         several population attributes.
        - 'proportion_file': a Population object is created by sampling
                            attributes from a specified distribution.
                            Proportions must be defined in a file 
                            specifying attribute's name and possible
                            values.
        - 'from_csv-: using a csv file where columns are attributes.

        Args:
            how (str, optional): . Defaults to 'basic'.
            population_size (int, optional): size of the population. Required
                                            if how is 'basic' or
                                            'proportion_file'.
                                             Defaults to None.
            network_seed (int, optional): random seed for the Network object.
                                          Defaults to 2048.
            population_seed (int, optional): random seed for the Population
                                             object. Defaults to 3069.
            pop_attributes (dict, optional): dictionary containing arrays with
                                             population attributes. Dict's
                                             keys are attribute labels and
                                             values must be numpy.Arrays.
                                             All arrays must be the same
                                             size. Defaults to None.
            filename (str, optional): name of the file to read from. Required
                                      if how='proportion_file'.
                                      Defaults to None.

        Raises:
            NotImplementedError
        """

        random.seed(network_random_seed)  # igraph seed
        stream = Stream(population_random_seed)
        if how == 'basic':
            self.population = Population(population_size, **network_kwargs)
        elif how == 'from_arrays':
            assert(isinstance(pop_attributes, dict))
            population_size = len(pop_attributes.items()[0][1])
            try:
                for key, val in pop_attributes.items():
                    assert(len(val) == population_size)
            except AssertionError:
                population_size = len(pop_attributes.items()[0][1])
            self.population = Population(population_size, **network_kwargs)
            for key, value in pop_attributes.items():
                self.population.add_attribute(key, value)
        elif how == 'proportion_file':
            assert(isinstance(filename, str))
            assert(isinstance(population_size, int))
            self.population = Population(population_size, **network_kwargs)
            pop_attributes, metadata = from_file_proportion(
                filename, population_size, stream)
            for key, value in pop_attributes.items():
                self.population.add_attribute(key, value)
        elif how == 'from_csv':
            assert(isinstance(filename, str))
            df = pd.read_csv(filename)
            self.population = Population(population_size=len(df), **network_kwargs)
            for c, v in df.items():
                self.population.add_attribute(c, v.values)
        else:
            raise NotImplementedError('Method not implemented')

    def add_intervention(self, InterventionCls: Type[Intervention],
                         time: Union[float, int], **intervention_kwargs):
        """ Method used to schedule an intervention. An intervention class
        is given, and the arguments to create the intervention object are
        passed as kwargs.

        Args:
            InterventionCls (Intervention class): Intervention class.
            time (float): simulation time to execute intervention.
        """
        try:
            assert(issubclass(InterventionCls, Intervention))
        except AssertionError:
            raise TypeError('Class must be inherit from the Intervention class.')
        InterventionCls(time, self, **intervention_kwargs)

    def add_disease(self, DiseaseCls: Type[AbstractDisease],
                    states_seed: np.ndarray[int] = None,
                    disease_kwargs: dict = {}):
        """ Method used to add a disease to the simulation. The user can
        define a seeding for the disease states.

        Args:
            DiseaseCls (_type_): _description_
            states_seed (_type_, optional): _description_. Defaults to None.
            disease_kwargs (dict, optional): _description_. Defaults to {}.

        Raises:
            ValueError: _description_
        """
        try:
            assert(not isinstance(self.population, type(None)))
        except AssertionError:
            raise ValueError(
                'Population not found.A population must be initialize first.')
        try:
            assert(issubclass(DiseaseCls, AbstractDisease))
        except AssertionError:
            raise TypeError('Class must inherit from the Disease class.')
        self.population.introduce_disease(
            DiseaseCls(self, **disease_kwargs),
            states_seed
            )

    def add_layer(self, layer_label: str, **kwargs):
        """ Method used to add a layer to the populaton network.
        Arguments to define how the layer is created are passed as kwargs.

        Args:
            layer_label (str): name of the layer.
        """
        if 'n' not in kwargs:
            kwargs['n'] = self.population.size
        self.population.network.add_layer(layer_label=layer_label, **kwargs)
