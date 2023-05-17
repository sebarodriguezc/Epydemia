from abc import ABC, abstractmethod
import numpy as np

class SelfObject():
    ''' doctring '''
    def __init__(self, attributes):
        ''' To be written '''
        self.attributes = {}
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

    @abstractmethod
    def do(self):
        pass


class Scheduler():
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
            if self.events_list[i].time > event.time:
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


class Simulator(ABC):

    def __init__(self, events=None):
        ''' events must be an iterable of events '''

        self.events = Scheduler()
        if not isinstance(events, type(None)):
            for e in events:
                self._add_event(e)

    def run(self, stop_time=float('inf')):

        self.sim_time = 0
        while (self.events.size() > 0):
            self.sim_time = self.events.next_event().time
            if self.sim_time <= stop_time:
                self.events.do_next()
            else:
                self.sim_time = stop_time
                break

    def now(self):
        return self.sim_time

    def _add_event(self, event):
        self.events.add(event)


class Stream(np.random.RandomState):

    def __init__(self, seed):
        super().__init__(seed=seed)


if __name__ == '__main__':


    sim = Simulator()

    s = Step(0.5, sim, 'A')
