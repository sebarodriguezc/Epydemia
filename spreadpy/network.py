import igraph as ig
import numpy as np
import random

class Network():
    random.seed(42)
    # Model school and other layers as attributes in edges? or as new graphs?

    def __init__(self):
        self.layers = dict()
        self.layers_names = []
        self.active_layers = []

    def __getitem__(self, key):
        ''' To be written '''
        return self.layers[key]

    def __setitem__(self, layer_name, new_layer):
        ''' To be written '''
        self.layers[layer_name] = new_layer
        self.layers_names.append(layer_name)
        self.active_layers.append(layer_name)

    def activate_layer(self, layer_name):
        assert(layer_name in self.layers_names)
        if layer_name not in self.activate_layer:
            self.active_layers.append(layer_name)

    def deactivate_layer(self, layer_name):
        assert(layer_name in self.layers_names)
        if layer_name not in self.activate_layer:
            self.active_layers.remove(layer_name)

    def add_random_layer(self, n, p, layer_name):
        self[layer_name] = ig.Graph.Erdos_Renyi(n=n, p=p)
        #self[layer_name].vs["id"] = list(range(n)) # Not sure if this is needed, igraph renumbers when deleting a vertex
    
    def add_attributes_edges(self, layer_name, attr_name, attrs):
        self[layer_name].es[attr_name] = attrs

    def get_edges(self, layer_name):
        # This must be modified to accept getting the edges of a subset of vertices
        edge_seq = self[layer_name].es
        vertex_seq = [[edge.source, edge.target] for edge in edge_seq]
        return edge_seq, vertex_seq
    

class Layer():

    def __init__(self, name):
        pass

    def