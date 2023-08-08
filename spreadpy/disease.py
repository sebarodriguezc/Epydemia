from . import SelfObject
from abc import ABC, abstractmethod

class Disease(SelfObject, ABC):
    ''' docstring '''

    def __init__(self, name, simulator, stream, infection_prob,
                 **attributes):
        # states
        self.name = name
        self.simulator = simulator
        self.stream = stream
        super().__init__(attributes)
        self['infection_prob'] = infection_prob

    @abstractmethod
    def progression(self):
        pass

    def update_transmission(self, population, edge_seq, vertex_seq):
        pass

    def initialize(self, population):
        pass
