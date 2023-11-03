from . import SubsObject, Simulator, Stream
from abc import ABC, abstractmethod
from typing import Any, Union, List, Tuple
import igraph as ig
import numpy as np
import random
from . import dict_to_csv


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
    def __init__(self, label: str, simulator: Simulator,
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
        self['states'] = {state:i for i,state in enumerate(states)}

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
                                           vertex_pair_seq:
                                           List[Tuple[int, int]]) -> Union[
                                               list, np.ndarray]:
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
        raise NotImplementedError

    @abstractmethod
    def initialize(self):
        """ Method used to conduct any operations when initializing
        the simulation.

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError
    
    def state_id(self, state_label: str) -> int:
        """ Mapper function to return the id of state.

        Args:
            state_label (str): label of the disease state.

        Returns:
            int: id representing state.
        """
        return self['states'][state_label]
    
    def set_random_state(self, seed: int):
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
        self.stream = Stream(seed=seed)


class Population(SubsObject):
    """ This class is used to represent the population of agents. Agents
    are represented using arrays, and therefore, the use of indeces is 
    needed to access attributes and correctly reference each agent. This
    class is also used to handle agent's attributes related with diseases,
    and handles the updating of tranmission probabilities in the network.

    It is assumed that the population remains constant during the simulation.
    However, a time-varying size can be implemented by modifying arrays
    accordingly.
    """

    def __init__(self, population_size: int, attributes: dict[str, Any] = {}):
        """ When initializing a Population object, a population size
        is needed. Any desired attributes must be given initially as
        a dictionary, where keys are an attribute's name and attribute
        values are numpy arrays of size equal to the population size.
        Additionaly attributes can be set by using the add_attributes
        method. 
        A Population object is associated with a Network object and
        tracks diseases through a dictionary containing Disease objects.

        Args:
            population_size (int): size of the population.
            attributes (dict, optional): dictionary with population
                                         attributes. Defaults to dict().
        """
        super().__init__(attributes=attributes)
        self.network = Network()
        self.size = population_size
        self.diseases = {}

    def add_attribute(self, attribute_label: str,
                      values: Any):
        """ Method used to add an attribute to the population.
        Attribute values must be given as a numpy array of length
        equal to the size of the population.

        Args:
            attribute_label (str): label to access the attribute.
            values (numpy.Array): attribute values.
        """
        if type(values) in [list, np.ndarray]:
            try:
                assert(len(values) == self.size)
            except AssertionError:
                raise IndexError(
                    "Array size ({}) doesn't match population size ({})"
                    .format(values.shape, self.size))
        self[attribute_label] = values

    def introduce_disease(self, disease: Disease, states_seed: int = None,
                          initial_state: str = 'susceptible'):
        """ Method used to introduce a disease in the population. It creates
        the data structures needed to keep track of each agent's disease
        state.
        When introducing a new disease, a population attribute (dict) with
        label the disease's name is created. The agent's disease states are
        stored in a numpy array in the latter dictionary, which can be access
        using the label states (i.e. self['disease.name']['states']). All
        population attributes associated with the disease are ment to be 
        saved in the corresponding disease dictionary).

        Args:
            disease (Disease object): disease to be introduced.
            states_seed (numpy.Array, optional): a population seed with
                                                agents initial states.
                                                Defaults to None.
            initial_state (str, optional): if no population seed is given,
                                           state which all agents' disease
                                           state will be set to.
        """

        try:
            assert issubclass(type(disease), Disease)
        except AssertionError:
            raise TypeError('Disease must be a Disease object')

        # Create data structure
        self.diseases[disease.label] = disease
        self[disease.label] = {}

        # Initialize states based on seed or an initial state
        if isinstance(states_seed, type(None)):
            try:
                self[disease.label] = \
                    np.full(self.size, disease.state_id(initial_state))
            except KeyError:
                raise KeyError("'{}' is not a state of {}".format(
                    initial_state, disease.label))
        else:
            assert(len(states_seed) == self.size)
            self[disease.label] = \
                np.array([disease.state_id(s) for s in states_seed])

        # Add probability of infection to the network
        for layer_label in self.network.layers.keys():
            self.network.add_attributes_edges(layer_label, disease.label,
                                              disease['infection_prob'])

    '''
    def __get_suceptible_prob(self, disease_name):
        def calc_prob(probs):
            return 1 - np.product([1-p for p in probs])

        susceptibles = np.where(
            self[disease_name]['states']  ==
            self.diseases[disease_name]['states']['susceptible'])[0]
        prob_infection = []

        for layer in self.network.get_active_layers():
            neighborhoods = layer.graph.neighborhood(susceptibles)  # check mode, should be undirected graph.

            neighborhoods = [
                [n for n in neighbors if self[disease_name]['states'][n] in
                 self.diseases[disease_name]['contagious_states']]
                for neighbors in neighborhoods]  # This line can be improved for efficiency

            prob_infection.append([
                calc_prob(layer.graph.es.select(
                 _source=person, _target=neighbors)[disease_name])
                for person, neighbors in zip(susceptibles, neighborhoods)])

        prob_infection = list(map(calc_prob, zip(*prob_infection)))
        return susceptibles, prob_infection
    '''
    '''
    def get_transmission_probability(self, disease_name):
        """ Method used to retrieve 

        Args:
            disease_name (_type_): _description_
        """
        def calc_prob(probs):
            return 1 - np.product([1-p for p in probs])

        susceptibles = np.where(
            self[disease_name]['states']  ==
            self.diseases[disease_name]['states']['susceptible'])[0]

        infected = np.where(
            np.isin(self[disease_name]['states'],
                    self.diseases[disease_name]['contagious_states']))[0]
        if len(infected) > 0:
            people_at_risk = np.unique(np.concatenate(
                [layer.graph.neighborhood(person)
                for layer in self.network.get_active_layers()
                for person in infected]))

            susceptibles = people_at_risk[np.where(
                self[disease_name]['states'][people_at_risk] ==
                self.diseases[disease_name]['states']['susceptible'])[0]]
        prob_infection = []

        for layer in self.network.get_active_layers():
            neighborhoods = layer.graph.neighborhood(susceptibles)  # check mode, should be undirected graph.

            neighborhoods = [
                [n for n in neighbors if self[disease_name]['states'][n] in
                 self.diseases[disease_name]['contagious_states']]
                for neighbors in neighborhoods]  # This line can be improved for efficiency

            prob_infection.append([
                calc_prob(layer.graph.es.select(
                 _source=person, _target=neighbors)[disease_name])
                for person, neighbors in zip(susceptibles, neighborhoods)])

        prob_infection = list(map(calc_prob, zip(*prob_infection)))
        return susceptibles, prob_infection
    '''

    def get_transmission_probabilities(self, disease_label: str,
                                       susceptible_states: List[str],
                                       infectee_states: List[str]) -> (
                                           np.ndarray, List[float]):
        """ Method used to retrieve the transmission probability between
        agents in any of the susceptibles states and agents in any of the
        infectious states for a certain disease.

        Args:
            disease_name (_type_): _description_
        """
        def calc_prob(probs: List[float]):
            return 1 - np.product([1-p for p in probs])

        susceptible_state_ids = [self.disease_state_id(disease_label, s)
                                 for s in susceptible_states]
        infectee_state_ids = [self.disease_state_id(disease_label, s)
                              for s in infectee_states]
        print('Using old')
        infected = np.where(
            np.isin(self[disease_label],
                    infectee_state_ids))[0]

        if len(infected) > 0:
            people_at_risk = np.unique(np.concatenate(
                [layer.graph.neighborhood(person)
                 for layer in self.network.get_active_layers()
                 for person in infected]))

            susceptibles = people_at_risk[np.where(
                np.isin(self[disease_label][people_at_risk],
                        susceptible_state_ids))[0]]
        else:
            susceptibles = np.array([])

        prob_infection = []

        for layer in self.network.get_active_layers():
            neighborhoods = layer.graph.neighborhood(susceptibles)  # check mode, should be undirected graph.

            neighborhoods = [
                [n for n in neighbors if self[disease_label][n] in
                 infectee_state_ids]
                for neighbors in neighborhoods]  # This line can be improved for efficiency

            prob_infection.append([
                calc_prob(layer.graph.es.select(
                 _source=person, _target=neighbors)[disease_label])
                for person, neighbors in zip(susceptibles, neighborhoods)])

        prob_infection = list(map(calc_prob, zip(*prob_infection)))
        return susceptibles, prob_infection

    def get_state(self, disease_label: str, state_label: str) -> np.ndarray:
        """ Method used to get the indices of agents that are currently
        on a specified disease state.

        Args:
            disease_name (str): name of the disease.
            state_name (str): state to search for.

        Returns:
            indices: numpy.Array with the indices of agents in that state.
        """
        return np.where(
            self[disease_label] ==
            self.diseases[disease_label].state_id(state_label))[0]

    def change_state(self, idx: Union[int, List[int]], disease_label: str,
                     state_label: str):
        """ Method used to change the disease state of a subset of agents.

        Args:
            idx (list or numpy.Array): list of indices of target agents.
            disease_name (str): name of the disease.
            state_name (str): state to change to.
        """
        self[disease_label][idx] = \
            self.disease_state_id(disease_label, state_label)

    def update_transmission_probabilities(self,
                                          disease_labels: List[str] = None,
                                          layer_labels: List[str] = None,
                                          target_vertex_seq: List[int] = None):
        """ Method used to update the transmission probabilities in the
        Network. Updates through the network are calculated based on each
        disease's update_transmission methods. It allows to the define a
        target based on a disease, layer or subset of agents (through their
        vertex indices). If no target is given, the method updates
        transmission weights for all diseases, layers and agents.

        Args:
            disease_names (str, optional): name of the target disease.
                                           Defaults to None.
            layer_names (str, optional): name of the target layer.
                                         Defaults to None.
            target_vertex_seq (list, optional): list of agents indices.
                                                Defaults to None.
        """

        if isinstance(disease_labels, type(None)):
            disease_labels = self.diseases.keys()
        if isinstance(layer_labels, type(None)):
            layer_labels = self.network.layers.keys()

        for layer_label in layer_labels:
            es, es_vertex_ids = self.network.get_edges(layer_label,
                                                       target_vertex_seq)
            for disease_label in disease_labels:
                new_p = self.diseases[
                    disease_label].compute_transmission_probabilities(
                    es_vertex_ids)
                self.network.add_attributes_edges(
                    layer_label, disease_label, new_p,
                    edge_seq=[e.index for e in es])

    def to_file(self, filename: str, var_labels: List[str]):
        """ Saves population to a file. A list of variable names/labels is
        needed to specify which attributes to save. If a disease name is
        given, the disease states array is saved.

        Args:
            filename (str): target filename to save.
            var_names (_type_): list with attributes names to save.
        """
        variables = {}
        for key in var_labels:
            variables[key] = self[key]
        dict_to_csv(variables, filename)

    def disease_state_id(self, disease_label: str, state_label: str) -> int:
        """ Wrapper function to get the id of a particular disease state.
        This must be used for indexing the population disease state attribute.

        Args:
            disease_label (str): label of the disease.
            state_label (str): state of the disease.

        Returns:
            int: _description_
        """
        return self.diseases[disease_label].state_id(state_label)


class Layer():
    """ Class used to handle each layer within a Network. It uses igraph's
    graph object to specify it's structure. The graph associated is assumed
    to be an undirected graph.
    Because the network uses indices to correlate agents with layers, all
    layers must have the same number of vertices.
    """

    def __init__(self, label: str, graph: ig.Graph):
        """ Creates a Layer object using a name and a graph.

        Args:
            name (str): name of the layer.
            graph (igraph.Graph): undirected graph object.
        """
        self.label = label
        self.active = True
        self.graph = graph

    def neighbors(self, vertex_seq: List[int], **kwargs) -> List[List[int]]:
        """ Method used to link igraph's neighborhood method.

        Args:
            vertex_seq (list): list containing the indices of the vertices.

        Returns:
            neighborhood: list with neighbors for each vertex. 
        """
        return self.graph.neighborhood(vertex_seq, **kwargs)


class Network:
    """ Class that handles the network structure of the agent based model.
    The network can hold for multiple layers, each one associated with an
    independent undirected graph object from igraph. Layers can be activated
    or deactivated for different uses. Each vertex represents an agent
    in the population, and each edge represents contacts between agents.
    Probability of infection for each disease are stored as attributes
    using as label the disease's name.

    The Network is meant to remain constant throughout the simulation, with
    changes in agents interactions modeled through alterations to the
    probability of infection (i.e. changing probability to zero when
    agent is in quarantine).

    The randomness is seeded using the Python's random module.
    """
    random.seed(42)

    def __init__(self):
        """ Creates a Network object.
        """
        self.layers = dict()
        self.layers_labels = []

    def __getitem__(self, key: str) -> Layer:
        """ Retrives an specific layer.

        Args:
            key (str): layer name.

        Returns:
            Layer (Layer.object): Desired layer.
        """
        return self.layers[key]

    def __setitem__(self, layer_label: str, new_layer: Layer):
        """Adds a layer to the network.

        Args:
            layer_label (str): label of the layer.
            new_layer (Layer.object): layer to add.
        """
        assert(isinstance(new_layer, Layer))
        self.layers[layer_label] = new_layer
        self.layers_labels.append(layer_label)

    def add_layer(self, layer_label: str, how: str = 'barabasi',
                  filename: str = None, graph: Any = None,
                  **kwargs):
        """ Method that adds a layer to the network through different ways.
        Implemented methods include creating random graphs using igraph's
        built-in method such as barabasi, erdos_renyi or k_regular, or
        by assigning a igraph object.

        Args:
            layer_name (str): layer name.
            how (str, optional): method used to create the graph for
                                 the layer. Defaults to 'barabasi'.

        Raises:
            ValueError: if 'graph' method is selected and no graph object
                        was passed as argument.
            NotImplementedError: _description_
        """
        if how == 'barabasi':
            self[layer_label] = Layer(label=layer_label,
                                     graph=ig.Graph.Barabasi(**kwargs))
        elif how == 'erdos_renyi':
            self[layer_label] = Layer(label=layer_label,
                                     graph=ig.Graph.Erdos_Renyi(**kwargs))
        elif how == 'k_regular':
            self[layer_label] = Layer(label=layer_label,
                                     graph=ig.K_Regular(**kwargs))
        elif how == 'graph':
            if type(graph) is not type(None):
                self[layer_label] = Layer(label=layer_label,
                                         graph=graph)
            else:
                raise ValueError(
                    "Must pass an igraph.Graph using the 'graph' argument")
        elif how == 'file':
                g = ig.Graph.Read_GraphML(filename)
                self[layer_label] = Layer(label=layer_label, graph=g)
        else:
            raise NotImplementedError('Method not implemented')

    def activate_layer(self, layer_label: str):
        """ Method used to change the state of a layer to active.

        Args:
            layer_name (str): name of the layer to activate.

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
            layer_name (str): name of the layer.

        Raises:
            KeyError: if layer is not found in network
        """
        try:
            self.layers[layer_label].active = False
        except KeyError:
            raise KeyError('Layer not found in the Network')

    def get_active_layers(self) -> List[Layer]:
        """ Method that returns layers that are active.

        Returns:
            active_layers: list of Layer objects that are active.
        """
        return [layer for key, layer in self.layers.items() if layer.active]

    def add_attributes_edges(self, layer_label: str, attr_label: str,
                             attrs: Union[list, np.ndarray],
                             edge_seq: List[int] = None):
        """ Method used to set the attribute values for a set of edges. If
        no edge sequence is provided, it assumes that the attribute is being
        set for all edges.

        Args:
            layer_name (str): name of the layer.
            attr_name (str): name of the attribute.
            attrs (iterable): list or array with attribute values.
            edge_seq (list, optional): list containing the indices of edges.
                                       Defaults to None.
        """
        if isinstance(edge_seq, type(None)):
            self[layer_label].graph.es[attr_label] = attrs
        else:
            self[layer_label].graph.es.select(edge_seq)[attr_label] = attrs

    def get_edges(self, layer_label: str,
                  target_vertex_seq: List[int] = None) -> (
                      ig.EdgeSeq, List[Tuple[int, int]]):
        """ Method used to get a set of edges. If a sequence of vertex
        ids are given, all edges containing those vertices. Because layers
        use undirected graphs, by retrieving edges with those vertices as
        source.

        Args:
            layer_label (str): name of the layer.
            target_vertex_seq (list, optional): list containing the
                                                index of the target vertices.
                                                Defaults to None.

        Returns:
           (edge_seq, vertex_seq): tuple containing the edge sequence igraph
                                   object, and a list with edges represented
                                   as tuples with its vertex ids.
        """
        if isinstance(target_vertex_seq, type(None)):
            edge_seq = self[layer_label].graph.es
        else:
            edge_seq = self[layer_label].graph.es.select(
                _source=target_vertex_seq)
        edge_seq_vertex_ids = [[edge.source, edge.target] for edge in edge_seq]
        return edge_seq, edge_seq_vertex_ids

    def get_neighbors(self, vertex_seq: List[int] = None,
                      layer_label: str = None, **kwargs) -> List[List[int]]:
        """ Method used to retrieve neighbors for a vertex sequence.

        Args:
            vertex_seq (list, optional): list containing the indices of the
                                         vertices. Defaults to None.
            layer_name (str, optional): name of the layer. Defaults to None.

        Returns:
            neighborhoods (list): list containing the list of neighbors for
                                each vertex.
        """
        if isinstance(layer_label, type(None)):
            search_layers = self.layers_labels
        else:
            search_layers = [layer_label]
        if isinstance(vertex_seq, type(None)):
            vertex_seq = [v.index for v in self[search_layers[0]].graph.vs]
        neighborhoods = list()
        for layer in search_layers:
            neighborhoods.append(self.layers[layer].neighbors(vertex_seq,
                                                              **kwargs))
        neighborhoods = [np.unique(np.concatenate([neighbors[i] for neighbors in neighborhoods]))
                         for i in np.arange(len(vertex_seq))]  # TODO: #17 This could be done more efficiently
        return neighborhoods


class StatsCollector(SubsObject):

    def collect(self, label: str, value: Any):
        if label not in self.attributes.keys():
            self[label] = [value]
        else:
            self[label].append(value)

    def clear(self):
        self.attributes = {}
