from . import SelfObject
from abc import ABC, abstractmethod

class Disease(SelfObject, ABC):
    ''' docstring '''

    def __init__(self, name, simulator, attributes, stream):
        # states
        self.name = name
        self.simulator = simulator
        super().__init__(attributes)
        self.stream = stream

    @abstractmethod
    def progression(self):
        pass

    def update_transmission(self, population, edge_seq, vertex_seq):
        pass
