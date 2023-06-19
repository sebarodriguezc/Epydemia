from . import SelfObject
from . import Disease
from . import Network
from . import Vaccination
from . import dict_to_csv
import numpy as np
import itertools
import igraph as ig

class Population(SelfObject):
    ''' docstring ''' 
    # Possible create vertices first and then create contact layers?
    # Network main or not will depend if there are different contact layers or not

    def __init__(self, population_size, attributes=dict()):
        ''' To be written '''
        # TODO: #7 implemente ability to initialize from file.
        super().__init__(attributes=dict())
        self.network = Network()
        self.population_size = population_size
        self.diseases = {}
        self._init_characteristics()

    def _init_characteristics(self):
        self['masking'] = np.zeros(self.population_size)
        self['quarantine'] = np.zeros(self.population_size)
    
    def add_attribute(self, attribute_name, values):
        assert(len(values) == self.population_size)
        self[attribute_name] = values

    def introduce_disease(self, disease, states_seed=None, vaccine_seed=None):
        '''Must be called when population has been created'''
        try:
            assert issubclass(type(disease), Disease)
        except AssertionError:
            raise ValueError('Must be a Disease object')
        self.diseases[disease.name] = disease
        self[disease.name] = {}

        if isinstance(states_seed, type(None)):
            self[disease.name]['states'] = np.full(
                self.population_size, disease['states']['susceptible'])
        else:
            assert(len(states_seed) == self.population_size)
            self[disease.name]['states'] = states_seed

        if isinstance(vaccine_seed, type(None)):
            self[disease.name]['vaccine'] = np.full(
                self.population_size,
                Vaccination.VACCINE_STATES['not vaccinated'])
        else:
            assert(len(vaccine_seed) == self.population_size)
            self[disease.name]['states'] = vaccine_seed

        for layer_name in self.network.layers.keys():  # Add probability
            self.network.add_attributes_edges(layer_name, disease.name,
                                              disease['infection_prob'])

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
    
    def get_suceptible_prob(self, disease_name):
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
        print(susceptibles)

        prob_infection = list(map(calc_prob, zip(*prob_infection)))
        return susceptibles, prob_infection

    def get_state(self, disease_name, state_name):
        return np.where(
            self[disease_name]['states'] ==
            self.diseases[disease_name]['states'][state_name])[0]

    def change_state(self, idx, disease_name, state_name):
        self[disease_name]['states'][idx] = self.diseases[
            disease_name]['states'][state_name]

    def plot_network(self, ax, layer, **plot_kwargs):
        ig.plot(self.network[layer].graph, target=ax, **plot_kwargs)

    def update_transmission_weights(self, disease_names=None, layer_names=None):
        # TODO: #3 implement that a subset of vertices can be updated.
        if isinstance(disease_names, type(None)):
            disease_names = self.diseases.keys()
        if isinstance(layer_names, type(None)):
            layer_names = self.network.layers.keys()

        for layer_name in layer_names:
            es, vs = self.network.get_edges(layer_name)
            for disease_name in disease_names:
                new_p = self.diseases[disease_name].update_transmission(
                    self, es, vs)  # TODO: #9 edges shouldn't be consider here
                self.network.add_attributes_edges(layer_name,
                                                  disease_name, new_p,
                                                  edge_seq=[e.index for e in es])
                # TODO: #10 The two lines above should be done in one function.

    def to_file(self, filename, var_names):
        variables = {}
        for key in var_names:
            if key in self.diseases.keys():
                variables[key] = self[key]['states']
            elif key in self.attributes.keys():
                variables[key] = self[key]
        dict_to_csv(variables, filename)
