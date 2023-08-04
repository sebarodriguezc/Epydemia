from . import SelfObject, Event, Stream
import numpy as np
from abc import ABC, abstractmethod

class Disease(SelfObject, ABC):
    ''' docstring '''

    def __init__(self, name, attributes):
        # states
        self.name = name
        super().__init__(attributes)

    @abstractmethod
    def progression(self):
        pass

    def update_transmission(self, population, edge_seq, vertex_seq):
        pass


class ChangeState(Event):

    def __init__(self, time, simulator, idx):
        super().__init__(time, simulator)
        self.time = time
        self.simulator = simulator
        self.idx = idx


