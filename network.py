import igraph as ig
import numpy as np
import random

class Network():
    random.seed(2)
    # Model school and other layers as attributes in edges? or as new graphs?

    def __init__(self):
        self.layers = dict()
        self.layers_names = []

    def __getitem__(self, key):
        ''' To be written '''
        return self.layers[key]

    def __setitem__(self, key, new_layer):
        ''' To be written '''
        self.layers[key] = new_layer
        self.layers_names.append(key)

    def add_random_layer(self, n, p, layer_name):
        self[layer_name] = ig.Graph.Erdos_Renyi(n=n, p=p)
        #self[layer_name].vs["id"] = list(range(n)) # Not sure if this is needed, igraph renumbers when deleting a vertex
    
    def add_attributes_edges(self, layer_name, attr_name, attrs):
        #random = np.random.random(len(self[layer_name].es)) 
        self[layer_name].es[attr_name] = attrs

    def get_edges(self, layer_name):
        edge_seq = self[layer_name].es
        vertex_seq = [[edge.source, edge.target] for edge in edge_seq]
        return edge_seq, vertex_seq