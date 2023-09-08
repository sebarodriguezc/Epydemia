from . import Event, Simulator
from typing import Union

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

    def __init__(self, time: Union[int, float], simulator: Simulator,
                 **kwargs):
        """ Intervention is initalized as an event requiring a time to be 
        executed and a simulator object. Kwargs are saved as a dict for used
        when executing event.

        Args:
            time (float): Simulation time at which event will be executed.
            simulator (_type_): _description_
        """
        super().__init__(time, simulator)
        self.kwargs = kwargs

    def do(self):
        """ Must override this method with the desired intervention's logic

        Raises:
            NotImplementedError:
        """
        raise NotImplementedError
