from . import Event, Simulator, Stream
from . import Population
from . import Intervention
from . import Disease
from . import StatsCollector
from . import from_file_proportion
import random


class Step(Event):
    """ Class that is used to define the step event. It's main purpose
    is to handle how the disease spreads across the population based on
    a user defined step logic (discrete, continuous), implemented through
    the do method. It also requires the user to implement an initialization
    class method, which is called at the beginning of the simulation. For
    example, in a discrete step the initialize method is used to schedule
    all discrete events until the end of the simulation.

    An example of a discrete daily step is given by the SampleDailyStep
    class defined in the special_events module.
    """

    def __init__(self, time, simulator):
        """ As the Step class inherits from the Event class, it requires
        an event time and a simulator object. This method can be 
        override by the user.

        Args:
            time (_type_): _description_
            simulator (_type_): _description_
        """
        super().__init__(time, simulator)

    def do(self):
        """ Method used to execute the logic of the step. Must be
        implemented by the user.

        Raises:
            NotImplementedError.
        """
        raise NotImplementedError

    @classmethod
    def initialize(cls, simulator, *args, **kwargs):
        """ Class method used to execute any initialization operations
        needed at the beginning of the simulation. It can be used to
        schedule all steps (discrete steps), schedule the first step
        (continuous step), or any logic designed by the user.

        Args:
            simulator (Simulator object): Simulator object where
                                          simulation is allocated.
        """
        pass


class AgentBasedSim(Simulator):
    """ Main simulation class. A AgentBasedSim object is used to handle
    all events (interventions) and run a simulation. It is also used to
    access objects across the simulation (i.e. population).

    It requires a Step class and a Population to run. The step class defines
    a step function that checks for new infected (daily step, continuous step,
    etc). The Step can also be used to update statistics (otherwise an
    intervention can be designed for this purpose).
    """

    def __init__(self, StepCls):
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

    def run(self, stop_time, verbose=True, seeds=(1024,)):
        """ Method called to run the simulation. It can be override by
        the user to implement additional operations.

        Args:
            stop_time (float): time until simulation is run. If an infinity
                                value is given, the simulaton will run until
                                no more events are schedulled.
            verbose (bool, optional): parameter used to activate the printing
                                      across the simulation. Defaults to True.
            seeds (tuple, optional): _description_. Defaults to (1024,).
        """
        self.verbose = verbose
        self.collector = StatsCollector()
        self.stop_time = stop_time

        #Covid.stream = Stream(seed=seeds[0])  # TODO: Assign streams for each disease class or object?

        self.step.initialize(self)
        super().run(self.stop_time)

    def create_population(self, how='basic', population_size=None,
                          network_seed=2048, population_seed=3069,
                          pop_attributes=None, filename=None, **kwargs):
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

    def add_disease(self, DiseaseCls, states_seed=None,
                    disease_kwargs={}):
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
            assert(issubclass(DiseaseCls, Disease))
        except AssertionError:
            raise TypeError('Class must inherit from the Disease class.')
        self.population.introduce_disease(
            DiseaseCls(self, **disease_kwargs),
            states_seed)

    def add_layer(self, layer_name, **kwargs):
        """ Method used to add a layer to the populaton network.
        Arguments to define how the layer is created are passed as kwargs.

        Args:
            layer_name (str): name of the layer.
        """
        if 'n' not in kwargs:
            kwargs['n'] = self.population.size
        self.population.network.add_layer(layer_name=layer_name, **kwargs)
