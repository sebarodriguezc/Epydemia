from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Union, Self, Callable, List


class SubsObject:
    """Definition of a subscriptable object to allow access to attributes
    using labels.
    """
    def __init__(self, attributes: dict = {}):
        """
        Args:
            attributes (dict, optional): dictionary with attributes. Defaults to {}.
        """
        self.attributes = {}
        for key, value in attributes.items():
            self.__setitem__(key, value)

    def __getitem__(self, key: str) -> Any:
        """Override of magic method

        Args:
            key (str): attribute's key

        Returns:
            Any: attribute object requested
        """

        return self.attributes[key]

    def __setitem__(self, key: str, newvalue: Any):
        """Override of magic method

        Args:
            key (str): attribute's key
            newvalue (Any): attribute object
        """
        self.attributes[key] = newvalue


class Simulator(ABC):
    """ Abstract class that governs the discrete event simulation framework.
    It allocates the events scheduler and must be used as main handler
    of the simulation.
    """

    def __init__(self):
        """ A simulator object is initialized with an empty scheduler and
        with a current simulation time of 0.
        """
        self.events = Scheduler()
        self.sim_time = 0

    def run(self, stop_time: Union[float, int] = float('inf')):
        """ Main method used to run a simulation. It is used to execute all
        events until:
        i) a specified stopping time or
        ii) all events have been executed.
        The current simulation time is updated upon execution of events.

        Args:
            stop_time (float, optional): simulation stopping time.
                                         Defaults to float('inf').
        """
        self.sim_time = 0
        while (self.events.size() > 0):
            self.sim_time = self.events.next_event().time
            if self.sim_time <= stop_time:
                self.events.do_next()
            else:
                self.sim_time = stop_time
                break
        self.events.clear()

    def now(self) -> float:
        """ Method used to return the current simulation time.

        Returns:
            float: _description_
        """
        return self.sim_time


class Event(ABC):
    """Abstract event class to use in a discrete simulation framework.
    User-defined events must inherit from this class.

    Args:
        ABC (class): implementation of python's abstract class
    """

    def __init__(self, time: Union[int, float], simulator: Simulator):
        """Event object initialization. The creation of an event must be
        preceded by the definition of a simulator object, which must be
        passed as an argument along with an event time. Upon creation of
        the event object, it is added to the simulator's event lists.

        Args:
            time (float): Simulation time at which event will be executed.
            simulator (Simulator.object): Simulator framework where events
                                          will be executed.
        """
        self.time = time
        self.simulator = simulator
        self.simulator.events.add_event(self)

    def __lt__(self, other_event: Self) -> bool:
        """Override of magic method to allow comparison of events using
        their execution time.

        Args:
            other_event (Event.object): event to compare against.

        Returns:
            boolean: If current event happens earlier than event
            compared against.
        """
        return self.time < other_event.time

    def __gt__(self, other: Self) -> bool:
        """Override of magic method to allow comparison of events using
        their execution time.

        Args:
            other_event (Event.object): event to compare against.

        Returns:
            boolean: If current event happens later than event
            compared against.
        """
        return self.time > other.time

    @abstractmethod
    def do(self):
        """ Method that defines what to do when event is executed.
        Must be implemented.

        Returns:
            None.
        """
        raise NotImplementedError


class Scheduler:
    """ Class that creates an event scheduler, which goal is to correctly
    handle events execution. Events are stored and sorted in a list, and
    are popped from it when events are schedulled to be exectued.
    """

    def __init__(self):
        """Initialization funtion. Core of the scheduler is a list.
        """
        self.events_list = list()

    def add_event(self, event: Event):
        """ Method used to schedule an event by adding it to the scheduler.

        Args:
            event (Event.object): event to be added.

        Raises:
            TypeError: checks if event object inherits from the Event class.
        """
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

    def cancel_event(self, event: Event):
        """ Method used to cancel an event from the scheduler. Object is
        removed from the events list.

        Args:
            event (Event.object): event to be cancelled.
        """
        self.events_list.remove(event)

    def clear(self):
        """ Method used to clear the events list from all schedulled events.
        """
        self.events_list = list()

    def size(self) -> int:
        """ Method used to determine the number of events present at
        the event_list.

        Returns:
            int: number of events yet to be executed
        """
        return len(self.events_list)

    def do_next(self):
        """ Method used to handle the execution of events.
        """
        if self.size() > 0:
            self.events_list.pop(0).do()
        else:
            print('No more events to be executed')

    def next_event(self):
        """ Method used to request the next event to be executed.

        Returns:
            Event.object: next event object to be executed.
        """
        try:
            return self.events_list[0]
        except IndexError:
            print('No more events to be executed')
            return None

    def sort(self):
        """ Sort the list of events in ascending order based on their times.
        """
        self.events_list.sort()

    def find(self, condition: Callable) -> List[Event]:
        """ Method used to find all events that meet a condition.

        Args:
            condition (callable function): callable function that accepts
            an event object as argument. Must return a boolean.

        Returns:
            list: list of events that meet the condition
        """
        try:
            assert(callable(condition))
        except AssertionError:
            raise ValueError('Condition must be a callable function.')
        return [e for e in self.events_list if condition(e)]


class Stream(np.random.RandomState):
    """ Class that defines a stream of pseudo-random numbers. It inherits from
    numpy's RandomState class which is used to sample random numbers from
    several probability distributions.

    Args:
        np.random.RandomState (class): numpy's random state class.
    """

    def __init__(self, seed: int):
        """ Stream object must be initialized using a seed.

        Args:
            seed (int): pseudo-random generator seed.
        """
        super().__init__(seed=seed)
        self.random_seed = seed

    def reset(self):
        self.seed(self.random_seed)
