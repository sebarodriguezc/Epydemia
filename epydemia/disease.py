from . import SubsObject, Simulator, Stream
from . import Population
from abc import ABC, abstractmethod
from typing import Any

class Disease(SubsObject, ABC):
    """ Abstract class used to define diseases. Disease classes are meant
    to hold all the information relative to infectious diseases. It is
    required that the user defines at least the disease progression states 
    and probability of infection through the network (which it is assumed to be
    a daily probability of someone getting infected by being in contact with
    a single infected agent. A different probability definition must go along
    with a proper definition of the simulation step).

    Args:
        SubsObject (class): Subscriptable object class.
        ABC (class): Python's built-in abstract class.
    """
    def __init__(self, name: str, simulator: Simulator, stream: Stream,
                 infection_prob: float, states: dict, **attributes: Any):
        """ Method that creates a disease object.

        Args:
            name (str): disease label
            simulator (Simulator): simulator object
            stream (Stream): stream object for pseudo-random numbers generation
            infection_prob (float): probability of infection (as defined
                                    by user). Must be between 0 and 1.
            states (dict): ditionary defining all possible disease states,
                           where keys are state labels (str) and values are
                           numeric (int) references to states.
        """
        super().__init__(attributes)
        self.name = name
        self.simulator = simulator
        self.stream = stream
        self['infection_prob'] = infection_prob
        self['states'] = states

    @abstractmethod
    def infect(self):
        """ Method used to trigger the progression of the disease on a subset
        of susceptible population. The key idea is that this method handles
        what happens when a new infection occurs. For example, in a daily
        step model, the progression of the disease will be updated at the end
        of each day by stochastically infecting those susceptibles who got in
        contact with infected people during the day.

        Raises:
            NotImplementedError: Must be implemented by the user.

        Returns:
            None
        """
        raise NotImplementedError

    @abstractmethod
    def compute_transmission_probabilities(self,
                                           population: Population,
                                           vertex_pair_seq:
                                           list[tuple[int, int]]):
        """ Method used to update the transmission probability throughout
        the network. Must return an iterable sequence with the infection
        probability corresponding to each vertex pair.
        A population object is needed to access any population attributes
        needed.

        Args:
            population (_type_): _description_
            vertex_pair_seq (list): list with tuples depicting edges through
                                    from and to nodes indeces. Note that the
                                    model uses undirected graphs.

        Raises:
            NotImplementedError: _description_

        Returns:
            new_infection_probabilities: iterable with the infection
                                         probabilities associated with edges.
        """
        raise NotImplementedError

    @abstractmethod
    def initialize(self, population):
        """ Method used to conduct any operations when initializing 
        the simulation.

        Args:
            population (Population object): population object.

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError
