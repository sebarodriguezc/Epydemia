from . import SubsObject
from . import Disease
from . import Network
#from . import VACCINE_STATES
from . import dict_to_csv
import numpy as np
import igraph as ig

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

    def __init__(self, population_size, attributes=dict()):
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
        super().__init__(attributes=dict())
        self.network = Network()
        self.size = population_size
        self.diseases = {}
        self._init_characteristics()

    def _init_characteristics(self):
        """ Method used to initialize basic characteristics of the
        population.
        """
        self['masking'] = np.zeros(self.size)
        self['quarantine'] = np.zeros(self.size)
    
    def add_attribute(self, attribute_name, values):
        """ Method used to add an attribute to the population.
        Attribute values must be given as a numpy array of length
        equal to the size of the population.

        Args:
            attribute_name (str): label/name to access the attribute.
            values (numpy.Array): attribute values.
        """
        try:
            assert(len(values) == self.size)
        except AssertionError:
            raise IndexError(
                "Array size ({}) doesn't match population size ({})".format(
                values.shape, self.size))
        self[attribute_name] = values

    def introduce_disease(self, disease, states_seed=None,
                          initial_state='susceptible'):
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
        self.diseases[disease.name] = disease
        self[disease.name] = {}

        # Initialize states based on seed or an initial state
        if isinstance(states_seed, type(None)):
            try:
                self[disease.name]['states'] = np.full(
                    self.size, disease['states'][initial_state])
            except KeyError:
                raise KeyError("'{}' is not a state of {}".format(
                    initial_state, disease.name))
        else:
            assert(len(states_seed) == self.size)
            self[disease.name]['states'] = states_seed

        # Execute any disease initialization
        disease.initialize(self)

        # Add probability of infection to the network
        for layer_name in self.network.layers.keys():
            self.network.add_attributes_edges(layer_name, disease.name,
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

    def get_suceptible_prob(self, disease_name):
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

    def get_state(self, disease_name, state_name):
        """ Method used to get the indices of agents that are currently
        on a specified disease state.

        Args:
            disease_name (str): name of the disease.
            state_name (str): state to search for.

        Returns:
            indices: numpy.Array with the indices of agents in that state.
        """
        return np.where(
            self[disease_name]['states'] ==
            self.diseases[disease_name]['states'][state_name])[0]

    def change_state(self, idx, disease_name, state_name):
        """ Method used to change the disease state of a subset of agents.

        Args:
            idx (list or numpy.Array): list of indices of target agents.
            disease_name (str): name of the disease.
            state_name (str): state to change to.
        """
        self[disease_name]['states'][idx] = self.diseases[
            disease_name]['states'][state_name]

    def update_transmission_weights(self, disease_names=None,
                                    layer_names=None, target_vertex_seq=None):
        """ Method used to update the transmission probabilities in the Network.
        Updates through the network are calculated based on each disease's
        update_transmission methods.
        It allows to the define a target based on a disease, layer or subset
        of agents (through their vertex indices). If no target is given,
        the method updates transmission weights for all diseases, layers and
        agents.

        Args:
            disease_names (str, optional): name of the target disease. Defaults to None.
            layer_names (str, optional): name of the target layer. Defaults to None.
            target_vertex_seq (list, optional): list of agents indices.
                                                Defaults to None.
        """

        if isinstance(disease_names, type(None)):
            disease_names = self.diseases.keys()
        if isinstance(layer_names, type(None)):
            layer_names = self.network.layers.keys()

        for layer_name in layer_names:
            es, vs = self.network.get_edges(layer_name, target_vertex_seq)
            for disease_name in disease_names:
                new_p = self.diseases[disease_name].update_transmission(
                    self, es, vs)  # TODO: #9 edges shouldn't be consider here
                self.network.add_attributes_edges(layer_name,
                                                  disease_name, new_p,
                                                  edge_seq=[e.index for e in es])

    def to_file(self, filename, var_names):
        """ Saves population to a file. A list of variable names/labels is
        needed to specify which attributes to save. If a disease name is 
        given, the disease states array is saved.

        Args:
            filename (str): target filename to save.
            var_names (_type_): list with attributes names to save.
        """
        variables = {}
        for key in var_names:
            if key in self.diseases.keys():
                variables[key] = self[key]['states']
            elif key in self.attributes.keys():
                variables[key] = self[key]
        dict_to_csv(variables, filename)
