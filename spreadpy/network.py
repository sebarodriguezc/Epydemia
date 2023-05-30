import igraph as ig
import numpy as np
import random

class Network():
    random.seed(42)

    def __init__(self):
        self.layers = dict()
        self.layers_names = []

    def __getitem__(self, key):
        ''' To be written '''
        return self.layers[key]

    def __setitem__(self, layer_name, new_layer):
        ''' To be written '''
        assert(isinstance(new_layer, Layer))
        self.layers[layer_name] = new_layer
        self.layers_names.append(layer_name)

    def add_layer(self, layer_name, how='random', **kwargs):
        if how == 'random':
            self[layer_name] = Layer(name=layer_name,
                                     graph=ig.Graph.Erdos_Renyi(**kwargs))

    def activate_layer(self, layer_name):
        assert(layer_name in self.layers_names)
        self.layers[layer_name].active = True

    def deactivate_layer(self, layer_name):
        assert(layer_name in self.layers_names)
        self.layers[layer_name].active = False

    def get_active_layers(self):
        return [layer for key, layer in self.layers.items() if layer.active]

    def add_attributes_edges(self, layer_name, attr_name, attrs, edge_seq=None):
        if isinstance(edge_seq, type(None)):
            self[layer_name].graph.es[attr_name] = attrs
        else:
            self[layer_name].graph.es.select(edge_seq)[attr_name] = attrs

    def get_edges(self, layer_name, target_vertex_seq=None):
        if isinstance(target_vertex_seq, type(None)):
            edge_seq = self[layer_name].graph.es
        else:
            edge_seq = self[layer_name].graph.es.select(
                _source=target_vertex_seq)
        vertex_seq = [[edge.source, edge.target] for edge in edge_seq]
        return edge_seq, vertex_seq


class Layer():

    def __init__(self, name, graph):
        self.name = name
        self.active = True
        self.graph = graph
