from abc import ABC, abstractmethod
from typing import List, Any, Tuple, Union, Type
from . import Stream, Simulator, SubsObject
import numpy as np


class AbstractLayer(ABC):

    def __init__(self, label: str):
        self.label = label
        self.active = True

    @abstractmethod
    def neighborhood(self, id_seq: List[int]) -> List[List[int]]:
        pass

    @abstractmethod
    def get_probability_of_infection(self, idx: int, neighbors: List[int], disease_label: str):
        pass

class AbstractDisease(SubsObject, ABC):
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

    def __init__(self, simulator: Simulator, label: str,
                 infection_prob: float, states: List[str],
                 **attributes: Any):
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
        self.label = label
        self.simulator = simulator
        self.population = simulator.population
        self.stream = None
        self['infection_prob'] = infection_prob
        self['states'] = {state: i for i, state in enumerate(states)}

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
        pass

    @abstractmethod
    def compute_transmission_probabilities(self,
                                           vertex_pair_seq:
                                           List[Tuple[int, int]]) -> Union[list, np.ndarray]:

        """ Method used to update the transmission probability throughout
        the network. Must return an iterable sequence with the infection
        probability corresponding to each vertex pair.
        A population object is needed to access any population attributes
        needed.

        Args:
            vertex_pair_seq (list): list with tuples depicting edges through
                                    from and to nodes indeces. Note that the
                                    model uses undirected graphs.

        Raises:
            NotImplementedError: _description_

        Returns:
            new_infection_probabilities: iterable with the infection
                                         probabilities associated with edges.
        """
        pass

    @abstractmethod
    def initialize(self):
        """ Method used to conduct any operations when initializing
        the simulation.

        Raises:
            NotImplementedError: _description_
        """
        pass

    def state_id(self, state_label: str) -> int:
        """ Mapper function to return the id of state.

        Args:
            state_label (str): label of the disease state.

        Returns:
            int: id representing state.
        """
        return self['states'][state_label]

    def set_stream(self, stream: Stream):
        """ Function used to create a stream of pseudo-random numbers.

        Args:
            seed (int): _description_

        Raises:
            IndexError: _description_
            TypeError: _description_
            KeyError: _description_
            ValueError: _description_
            NotImplementedError: _description_
            KeyError: _description_
            KeyError: _description_

        Returns:
            _type_: _description_
        """
        self.stream = stream


class AbstractNetwork(ABC):

    def __init__(self):
        self.layers = {}
        self.layers_labels = []

    def __getitem__(self, key: str) -> AbstractLayer:
        """ Retrives an specific layer.

        Args:
            key (str): layer name.

        Returns:
            Layer (Layer.object): Desired layer.
        """
        return self.layers[key]

    def __setitem__(self, layer_label: str, new_layer: AbstractLayer):
        """Adds a layer to the network.

        Args:
            layer_label (str): label of the layer.
            new_layer (Layer.object): layer to add.
        """
        assert (isinstance(new_layer, AbstractLayer))
        self.layers[layer_label] = new_layer
        self.layers_labels.append(layer_label)

    def activate_layer(self, layer_label: str):
        """ Method used to change the state of a layer to active.

        Args:
            layer_label (str): name of the layer to activate.

        Raises:
            KeyError: if layer is not found in network
        """
        try:
            self.layers[layer_label].active = True
        except KeyError:
            raise KeyError('Layer not found in the Network')

    def deactivate_layer(self, layer_label: str):
        """ Method used to change the state of a layer to deactivated.

        Args:
            layer_label (str): name of the layer.

        Raises:
            KeyError: if layer is not found in network
        """
        try:
            self.layers[layer_label].active = False
        except KeyError:
            raise KeyError('Layer not found in the Network')

    def get_active_layers(self) -> List[AbstractLayer]:
        """ Method that returns layers that are active.

        Returns:
            active_layers: list of Layer objects that are active.
        """
        return [layer for key, layer in self.layers.items() if layer.active]

    @abstractmethod
    def add_layer(self, **kwargs):
        pass

    @abstractmethod
    def initialize(self, diseases: dict, **kwargs):
        pass

    @abstractmethod
    def get_neighborhood(self, id_seq: List[int] = None, layer_label: str = None, **kwargs) -> List[List[int]]:
        pass

    @abstractmethod
    def update_transmission_probability(self,
                                        diseases: List[AbstractDisease],
                                        layer_labels: List[str],
                                        target_ids: List[int]):
        pass
