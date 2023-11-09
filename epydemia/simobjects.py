from . import SubsObject
from typing import Any, Union, List, Tuple
import igraph as ig
import numpy as np
import random
from . import dict_to_csv
from . import AbstractLayer, AbstractNetwork, AbstractDisease

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

    def __init__(self, population_size: int, attributes: dict[str, Any] = {}, **network_kwargs):
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
        self.network = Network(**network_kwargs)
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

    def introduce_disease(self, disease: AbstractDisease, states_seed: int = None,
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
            assert issubclass(type(disease), AbstractDisease)
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

    # def get_transmission_probabilities(self, disease_label: str,
    #                                    susceptible_states: List[str],
    #                                    infectee_states: List[str]) -> (
    #                                        np.ndarray, List[float]):
    #     """ Method used to retrieve the transmission probability between
    #     agents in any of the susceptibles states and agents in any of the
    #     infectious states for a certain disease.
    #
    #     Args:
    #         disease_name (_type_): _description_
    #     """
    #     def calc_prob(probs: List[float]):
    #         return 1 - np.product([1-p for p in probs])
    #
    #     susceptible_state_ids = [self.disease_state_id(disease_label, s)
    #                              for s in susceptible_states]
    #     infectee_state_ids = [self.disease_state_id(disease_label, s)
    #                           for s in infectee_states]
    #
    #     susceptibles = np.where(
    #         np.isin(self[disease_label], susceptible_state_ids))[0]
    #
    #     prob_infection = []
    #
    #     for layer in self.network.get_active_layers():
    #         neighborhoods = self.network.get_neighborhood(susceptibles, layer=layer)  # check mode, should be undirected graph.
    #
    #         neighborhoods = [
    #             [n for n in neighbors if self[disease_label][n] in
    #              infectee_state_ids]
    #             for neighbors in neighborhoods]  # This line can be improved for efficiency
    #
    #         prob_infection.append([
    #             calc_prob(layer.graph.es.select(
    #              _source=person, _target=neighbors)[disease_label])
    #             for person, neighbors in zip(susceptibles, neighborhoods)])
    #
    #     prob_infection = list(map(calc_prob, zip(*prob_infection)))
    #     return susceptibles, prob_infection

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

        infected = np.where(
            np.isin(self[disease_label],
                    infectee_state_ids))[0]
        print('Using updated')

        if len(infected) > 0:
            people_at_risk = np.unique(np.concatenate(
                [np.concatenate(self.network.get_neighborhood(infected, layer_label=layer.label))
                 for layer in self.network.get_active_layers()]))

            susceptibles = people_at_risk[np.where(
                np.isin(self[disease_label][people_at_risk],
                        susceptible_state_ids))[0]]
        else:
            susceptibles = np.array([])
        prob_infection = []
        print('Infected', infected)

        for layer in self.network.get_active_layers():
            neighborhoods = self.network.get_neighborhood(susceptibles, layer_label=layer.label)  # check mode, should be undirected graph.
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


class Layer(AbstractLayer):
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
        super().__init__(label)
        self.graph = graph

    def neighborhood(self, id_seq: List[int], **kwargs) -> List[List[int]]:
        """ Method used to link igraph's neighborhood method.

        Args:
            id_seq (list): list containing the indices of the vertices.

        Returns:
            neighborhood: list with neighbors for each vertex. 
        """
        return self.graph.neighborhood(id_seq, **kwargs)


class Network(AbstractNetwork):
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
        super().__init__()

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

    def initialize(self, **kwargs):
        pass
        # if self.precompute_neighbors:
        #     self.neighborhood_by_layer = {}
        #     for layer_label, layer in self.layers.items():
        #         id_seq = [v.index for v in layer.graph.vs]
        #         self.neighborhood_by_layer[layer_label] = dict(zip(id_seq, layer.neighborhood(id_seq, **kwargs)))
        #     self.neighborhood = {i: np.unique(
        #         np.concatenate([self.neighborhood_by_layer[layer][i] for layer in self.layers_labels])) for i in id_seq}

    def add_attributes_edges(self, layer_label: str, attr_label: str,
                             attrs: Union[list, np.ndarray],
                             edge_seq: List[int] = None):
        """ Method used to set the attribute values for a set of edges. If
        no edge sequence is provided, it assumes that the attribute is being
        set for all edges.

        Args:
            layer_label (str): name of the layer.
            attr_label (str): name of the attribute.
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

    def get_neighborhood(self, id_seq: List[int] = None,
                      layer_label: str = None, **kwargs) -> List[List[int]]:
        """ Method used to retrieve neighbors for a vertex sequence.

        Args:
            id_seq (list, optional): list containing the indices of the
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
        if isinstance(id_seq, type(None)):
            id_seq = [v.index for v in self[search_layers[0]].graph.vs]
        if self.precompute_neighbors:
            if len(search_layers) == 1:
                return [self.neighborhood_by_layer[search_layers[0]][i] for i in id_seq]
            else:
                return [self.neighborhood[i] for i in id_seq]
        else:
            neighborhoods = list()
            for layer in search_layers:
                neighborhoods.append(self.layers[layer].neighborhood(id_seq, **kwargs))
            neighborhoods = [np.unique(np.concatenate([neighbors[i] for neighbors in neighborhoods]))
                             for i in np.arange(len(id_seq))]  # TODO: #17 This could be done more efficiently
            return neighborhoods


class StatsCollector(SubsObject):

    def collect(self, label: str, value: Any):
        if label not in self.attributes.keys():
            self[label] = [value]
        else:
            self[label].append(value)

    def clear(self):
        self.attributes = {}
