from abc import ABC, abstractmethod
import numpy as np

class SelfObject():
    ''' doctring '''
    def __init__(self, attributes=None):
        ''' To be written '''
        self.attributes = {}
        if not isinstance(attributes, type(None)):
            assert isinstance(attributes, dict)
            for key, value in attributes.items():
                self.__setitem__(key, value)

    def __getitem__(self, key):
        ''' To be written '''
        return self.attributes[key]

    def __setitem__(self, key, newvalue):
        ''' To be written '''
        self.attributes[key] = newvalue


class Event(ABC):
    ''' docstring '''

    def __init__(self, time, simulator):
        self.time = time
        simulator._add_event(self)

    def __lt__(self, other):
        return self.time < other.time

    def __gt__(self, other):
        return self.time > other.time

    @abstractmethod
    def do(self):
        pass


class Scheduler():
    # Could inherit from list?
    ''' docstring '''

    def __init__(self):
        self.events_list = list()

    def add(self, event):
        try:
            assert isinstance(event, Event)
        except AssertionError:
            raise TypeError('Not an Event type object')
        i = 0
        while i < self.size():
            if self.events_list[i] > event:
                break
            i += 1
        self.events_list.insert(i, event)

    def cancel(self, event):
        self.events_list.remove(event)

    def clear(self):
        self.events_list = list()

    def size(self):
        return len(self.events_list)

    def do_next(self):
        self.events_list.pop(0).do()

    def next_event(self):
        try:
            return self.events_list[0]
        except Exception:
            return None #Raise error?

    def sort(self):
        self.events_list.sort()

    def find(self, condition):
        assert(callable(condition))
        return [e for e in self.events_list if condition(e)]


class Simulator(ABC):

    def __init__(self):
        ''' events must be an iterable of events '''
        self.events = Scheduler()

    def run(self, stop_time=float('inf')):

        self.sim_time = 0
        while (self.events.size() > 0):
            self.sim_time = self.events.next_event().time
            if self.sim_time <= stop_time:
                self.events.do_next()
            else:
                self.sim_time = stop_time
                break
        self.events.clear()

    def now(self):
        return self.sim_time

    def _add_event(self, event):
        self.events.add(event)

    def cancel_event(self, event):
        self.events.cancel(event)


class Stream(np.random.RandomState):

    def __init__(self, seed):
        super().__init__(seed=seed)
        self.seed = seed
    


if __name__ == '__main__':
    
    class Eventz(Event):
        idx_counter = 1

        def __init__(self, time, simulator):
            super().__init__(time, simulator)
            self.idx = Eventz.idx_counter
            Eventz.idx_counter += 1

        def do(self):
            print('Hello {}'.format(self.time))

    sim = Simulator()
    e1 = Eventz(1, sim)
    e2 = Eventz(5, sim)
    e3 = Eventz(6, sim)
    e1.time = 5.5
    sim.events.sort()

    print([e.time for e in sim.events.events_list])
