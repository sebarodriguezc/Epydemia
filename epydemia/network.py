import igraph as ig
import numpy as np
import random

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
        self.layers_names = []

    def __getitem__(self, key):
        """ Retrives an specific layer.

        Args:
            key (str): layer name.

        Returns:
            Layer (Layer.object): Desired layer.
        """
        return self.layers[key]

    def __setitem__(self, layer_name, new_layer):
        """Adds a layer to the network.

        Args:
            layer_name (str): layer name.
            new_layer (Layer.object): layer to add.
        """
        assert(isinstance(new_layer, Layer))
        self.layers[layer_name] = new_layer
        self.layers_names.append(layer_name)

    def add_layer(self, layer_name, how='barabasi', **kwargs):
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
            self[layer_name] = Layer(name=layer_name,
                                     graph=ig.Graph.Barabasi(**kwargs))
        elif how == 'erdos_renyi':
            self[layer_name] = Layer(name=layer_name,
                                     graph=ig.Graph.Erdos_Renyi(**kwargs))
        elif how == 'k_regular':
            self[layer_name] = Layer(name=layer_name,
                                     graph=ig.K_Regular(**kwargs))
        elif how == 'graph':
            try:
                self[layer_name] = Layer(name=layer_name,
                                         graph=kwargs['graph'])
            except KeyError:
                raise ValueError(
                    "Must pass an igraph.Graph using the 'graph' argument")
        else:
            raise NotImplementedError('Method not implemented')

    def activate_layer(self, layer_name):
        """ Method used to change the state of a layer to active.

        Args:
            layer_name (str): name of the layer to activate.

        Raises:
            KeyError: if layer is not found in network
        """
        try:
            self.layers[layer_name].active = True
        except KeyError:
            raise KeyError('Layer not found in the Network')

    def deactivate_layer(self, layer_name):
        """ Method used to change the state of a layer to deactivated.

        Args:
            layer_name (str): name of the layer.

        Raises:
            KeyError: if layer is not found in network
        """
        try:
            self.layers[layer_name].active = False
        except KeyError:
            raise KeyError('Layer not found in the Network')

    def get_active_layers(self):
        """ Method that returns layers that are active.

        Returns:
            active_layers: list of Layer objects that are active.
        """
        return [layer for key, layer in self.layers.items() if layer.active]

    def add_attributes_edges(self, layer_name, attr_name, attrs,
                             edge_seq=None):
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
            self[layer_name].graph.es[attr_name] = attrs
        else:
            self[layer_name].graph.es.select(edge_seq)[attr_name] = attrs

    def get_edges(self, layer_name, target_vertex_seq=None):
        """ Method used to get a set of edges. If a sequence of vertex
        ids are given, all edges containing those vertices. Because layers
        use undirected graphs, by retrieving edges with those vertices as
        source.

        Args:
            layer_name (str): name of the layer.
            target_vertex_seq (list, optional): list containing the
                                                index of the target vertices.
                                                Defaults to None.

        Returns:
           (edge_seq, vertex_seq): tuple containing the edge sequence igraph
                                   object, and a list with edges represented
                                   as tuples with its vertex ids.
        """
        if isinstance(target_vertex_seq, type(None)):
            edge_seq = self[layer_name].graph.es
        else:
            edge_seq = self[layer_name].graph.es.select(
                _source=target_vertex_seq)
        edge_seq_vertex_ids = [[edge.source, edge.target] for edge in edge_seq]
        return edge_seq, edge_seq_vertex_ids
    
    def get_neighbors(self, vertex_seq=None, layer_name=None, **kwargs):
        """ Method used to retrieve neighbors for a vertex sequence.

        Args:
            vertex_seq (list, optional): list containing the indices of the
                                         vertices. Defaults to None.
            layer_name (str, optional): name of the layer. Defaults to None.

        Returns:
            neighborhoos (list): list containing the list of neighbors for
                                each vertex.
        """
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
    """ Class used to handle each layer within a Network. It uses igraph's graph
    object to specify it's structure. The graph associated is assumed to be an
    undirected graph.
    Because the network uses indices to correlate agents with layers, all layers
    must have the same number of vertices.
    """

    def __init__(self, name, graph):
        """ Creates a Layer object using a name and a graph.

        Args:
            name (str): name of the layer.
            graph (igraph.Graph): undirected graph object.
        """
        self.name = name
        self.active = True
        self.graph = graph

    def neighbors(self, vertex_seq, **kwargs):
        """ Method used to link igraph's neighborhood method.

        Args:
            vertex_seq (list): list containing the indices of the vertices.

        Returns:
            neighborhood: list with neighbors for each vertex. 
        """
        return self.graph.neighborhood(vertex_seq, **kwargs)
