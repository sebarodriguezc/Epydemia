from base import SelfObject
from disease import Disease
import numpy as np
from network import Network
import itertools

class Population(SelfObject):
    ''' docstring ''' 
    # Possible create vertices first and then create contact layers?
    # Network main or not will depend if there are different contact layers or not
    # if mulitple layeres, then must iterate over all layers to get prob.

    def __init__(self, population_size):
        ''' To be written '''
        super().__init__(attributes=dict())
        self.network = Network()
        self.population_size = population_size
        self.diseases = {}

    def create_random_contact_layer(self, v=None, p=0.1, layer_name='main'):
        ''' should be given the option to give the vertices' id to do a new layer'''
        self.network.add_random_layer(self.population_size, p, layer_name)

    def introduce_disease(self, disease):
        '''Must be called when population has been created'''
        assert issubclass(type(disease), Disease)
        self.diseases[disease.name] = disease
        self[disease.name] = {}
        self[disease.name]['states'] = np.full(self.population_size,
                                    disease['states']['susceptible'])

        # For each layer, add probability attribute with name of the disease
        for layer_name in self.network.layers.keys():
            self.network.add_attributes_edges(layer_name, disease.name, disease['infection_prob'])

    def get_suceptible_prob(self, disease_name):
        def calc_prob(probs):
            return 1 - np.product([1-p for p in probs])

        susceptibles = np.where(self[disease_name]['states']  ==
                                self.diseases[disease_name]['states']['susceptible'])[0]
        prob_infection = []
        for layer in self.network.layers.keys():
            neighborhoods = self.network[layer].neighborhood(susceptibles)  # check mode, should be undirected graph.

            neighborhoods = [
                [n for n in neighbors if self[disease_name]['states'][n] in
                self.diseases[disease_name]['contagious_states']]
                for neighbors in neighborhoods] #This line can be improved for efficiency

            prob_infection.append([
                calc_prob(self.network[layer].es.select(_source=person,
                                                        _target=neighbors)[disease_name])
                for person, neighbors in zip(susceptibles, neighborhoods)])
        prob_infection = list(map(calc_prob, zip(*prob_infection)))
        return susceptibles, prob_infection

    def get_state(self, disease_name, state_name):
        return np.where(self[disease_name]['states']  ==
                                self.diseases[disease_name]['states'][state_name])[0]

    #def infect(self, idx, disease_name):
    #    self[disease_name]['states'][idx] = self.diseases[disease_name]['states']['infected']

    def change_state(self, idx, disease_name, state_name):
        self[disease_name]['states'][idx] = self.diseases[disease_name]['states'][state_name]

    def plot_network(self, ax, layer='main'):
        ig.plot(self.network[layer], layout=self.network[layer].layout('kk'), target=ax)