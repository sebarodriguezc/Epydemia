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
                                     graph=ig.Graph.Barabasi(**kwargs))

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

    def get_neighbors(self, vertex_seq=None, layer_name=None, **kwargs):
        if isinstance(layer_name, type(None)):
            search_layers = self.layers_names
        else:
            search_layers = [layer_name]
        if isinstance(vertex_seq, type(None)):
            vertex_seq = [v.index for v in self[search_layers[0]].graph.vs]
        neighborhoods = list()
        for layer in search_layers:
            neighborhoods.append(self.layers[layer].neighbors(vertex_seq,
                                                              **kwargs))
        neighborhoods = [np.unique(np.concatenate([neighbors[i] for neighbors in neighborhoods]))
                         for i in np.arange(len(vertex_seq))]  # TODO: #17 This could be done more efficiently
        return neighborhoods


class Layer():

    def __init__(self, name, graph):
        self.name = name
        self.active = True
        self.graph = graph

    def neighbors(self, vertex_seq, **kwargs):
        return self.graph.neighborhood(vertex_seq, **kwargs)  # check mode, should be undirected graph.
