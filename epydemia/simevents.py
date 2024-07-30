from . import Event, Simulator
from . import AbstractDisease
import numpy as np
from typing import Union


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

    def __init__(self, simulator: Simulator, time: Union[float, int]):
        """ As the Step class inherits from the Event class, it requires
        an event time and a simulator object. This method can be
        override by the user.

        Args:
            time (_type_): _description_
            simulator (_type_): _description_
        """
        super().__init__(simulator, time)

    def do(self):
        """ Method used to execute the logic of the step. Must be
        implemented by the user.

        Raises:
            NotImplementedError.
        """
        raise NotImplementedError

    @classmethod
    def initialize(cls, simulator: Simulator, *args, **kwargs):
        """ Class method used to execute any initialization operations
        needed at the beginning of the simulation. It can be used to
        schedule all steps (discrete steps), schedule the first step
        (continuous step), or any logic designed by the user.

        Args:
            simulator (Simulator object): Simulator object where
                                          simulation is allocated.
        """
        pass


class Intervention(Event):
    """ Class used to model intervention events such as beginning of
    quarantine, changes in transmission dynamics, vaccinations, etc.
    As the framework is based on a discrete-event simulation paradigm,
    the modeling of interventions must follow the logic of a unique event.
    Hence, interventions that modify attributes over a specific time
    window must be modeled using two interventions: one starting the
    intervention and another to end it.

    Args:
        Event (_type_): _description_
    """

    def __init__(self, simulator: Simulator, time: Union[int, float],
                 **kwargs):
        """ Intervention is initalized as an event requiring a time to be
        executed and a simulato/r object. Kwargs are saved as a dict for used
        when executing event.78

        Args:
            time (float): Simulation time at which event will be executed.
            simulator (_type_): _description_
        """
        super().__init__(simulator, time)
        self.kwargs = kwargs
        #TODO: add access to population and network through attributes.

    def do(self):
        """ Must override this method with the desired intervention's logic

        Raises:
            NotImplementedError:
        """
        raise NotImplementedError


class SampleDailyStep(Step):

    STEP_SIZE = 1

    def __init__(self, simulator: Simulator, time: Union[float, int]):
        super().__init__(simulator, time)

    @classmethod
    def initialize(cls, simulator: Simulator):
        for t in np.arange(0, int(simulator.stop_time)+1,
                           SampleDailyStep.STEP_SIZE):
            SampleDailyStep(simulator, t)

    def do(self):
        for _, disease in self.simulator.population.diseases.items():
            disease.infect()


class ChangeState(Event):

    def __init__(self, simulator: Simulator, time: Union[float, int], idx: int):
        super().__init__(simulator, time)
        self.idx = idx
        self.population = self.simulator.population

    def do(self):
        pass

class ImportCases(Event):

    def __init__(self, simulator: Simulator, time: Union[float, int],
                 disease_label: str, change_state_event: ChangeState.__class__,
                 num_cases: int):
        super().__init__(simulator, time)
        self.time = time
        self.population = self.simulator.population
        self.num_cases = num_cases
        self.disease_label = disease_label
        self.change_state_event = change_state_event

    def do(self):
        susceptibles = self.population.get_state(self.disease_label, 'susceptible')
        idx = self.simulator.streams[self.disease_label].choice(
            susceptibles, size=self.num_cases, replace=False)
        for person in idx:
            self.change_state_event(self.simulator, self.simulator.now(), person)
            if self.simulator.verbose:
                print('Agent {} got infected outside of the network'.format(person))
