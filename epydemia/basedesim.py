from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Union, Self, Callable, List, Optional
from datetime import datetime
import pickle

class SubsObject:
    """Definition of a subscriptable object to allow access to attributes
    using labels.
    """
    def __init__(self, attributes: Optional[dict] = None):
        """
        Args:
            attributes (dict, optional): dictionary with attributes. Defaults to {}.
        """
        self.attributes = {}
        if attributes is not None:
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

    def __setitem__(self, key: str, new_value: Any):
        """Override of magic method

        Args:
            key (str): attribute's key
            new_value (Any): attribute object
        """
        self.attributes[key] = new_value


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

    def reseed(self, seed: int):
        self.random_seed = seed
        self.reset()


class StreamsManager:

    def __init__(self, labels: Optional[Union[list, dict]] = None):
        if type(labels) == list:
            self.streams = {label: Stream(seed=0) for label in labels}
        elif type(labels) == dict:
            self.streams = {label: Stream(seed=seed) for label, seed in labels.items()}
        else:
            self.streams = {}

    def __getitem__(self, key: str) -> Any:
        """Override of magic method

        Args:
            key (str): attribute's key

        Returns:
            Any: attribute object requested
        """

        return self.streams[key]

    def __setitem__(self, key: str, new_value: Stream):
        """Override of magic method

        Args:
            key (str): attribute's key
            newvalue (Any): attribute object
        """
        self.streams[key] = new_value

    def reset_streams(self):
        for key, stream in self.streams.items():
            stream.reset()

    def reseed(self, new_seed: dict):
        for label, seed in new_seed.items():
            self.streams[label].reseed(seed)

    def generate_seeds(self, labels: List[str], n_seeds: int, start: Optional[int] = 0):
        arr = np.array_split(np.arange(start, len(labels)*n_seeds), len(labels))
        return [{label: arr[j][i] for j, label in enumerate(labels)} for i in range(n_seeds)]


class Simulator(ABC):
    """ Abstract class that governs the discrete event simulation framework.
    It allocates the events scheduler and must be used as main handler
    of the simulation.
    """

    def __init__(self, streams: Optional[StreamsManager] = None):
        """ A simulator object is initialized with an empty scheduler and
        with a current simulation time of 0.
        """
        if streams is None:
            self.streams = StreamsManager()
        else:
            self.streams = streams
        self.events = Scheduler()
        self.pre_scheduled_events = []
        self.sim_time = np.nan
        self.params = {}
        self.verbose = False

    def _initialize(self, seeds: Optional[dict] = None):
        self.clear()
        self.sim_time = 0
        for EventCls, kwargs in self.pre_scheduled_events:
            EventCls(self, **kwargs)
        if seeds is not None:
            self.streams.reseed(seeds)

    def run(self, stop_time: Union[float, int], seeds: Optional[dict] = None,
            verbose: bool = False):
        """ Main method used to run a simulation. It is used to execute all
        events until:
        i) a specified stopping time or
        ii) all events have been executed.
        The current simulation time is updated upon execution of events.

        Args:
            stop_time (float, optional): simulation stopping time.
                                         Defaults to float('inf').
        """
        self.verbose = verbose
        self._initialize(seeds=seeds)
        while self.events.size() > 0:
            self.sim_time = self.events.next_event().time
            if self.sim_time <= stop_time:
                self.events.do_next()
            else:
                self.sim_time = stop_time
                break

    def now(self) -> float:
        """ Method used to return the current simulation time.

        Returns:
            float: _description_
        """
        return self.sim_time

    def clear(self):
        self.streams.reset_streams()
        self.events.clear()

    def get_stream(self, label: str):
        return self.streams[label]

    def set_stream(self, label: str, seed: int):
        self.streams[label] = Stream(seed=seed)

    def pre_schedule_event(self, event_cls, **kwargs):
        self.pre_scheduled_events.append((event_cls, kwargs))

    def set_param(self, label: str, param: Any):
        self.params[label] = param

    def dump_stats(self):
        pass #TODO: Implement a collector class that dumps stats here.



class Event(ABC):
    """
    Abstract event class to use in a discrete simulation framework.
    User-defined events must inherit from this class.

    Args:
        ABC (class): implementation of python's abstract class
    """

    def __init__(self, simulator: Simulator, time: Union[int, float]):
        """
        Event object initialization. The creation of an event must be
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
        """
        Override of magic method to allow comparison of events using
        their execution time.

        Args:
            other_event (Event.object): event to compare against.

        Returns:
            boolean: If current event happens earlier than event
            compared against.
        """
        return self.time < other_event.time

    def __gt__(self, other: Self) -> bool:
        """
        Override of magic method to allow comparison of events using
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
        """ Method used to clear the events list from all scheduled events.
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


class Experiment:

    def __init__(self, sim: Simulator, experiment_name: str):
        self.sim = sim
        self.experiment_name = experiment_name
        self.results = []

    def run(self, stop_time: Union[int, float], n_replicas: int, seeds: list,
            verbose: bool = True):
        assert len(seeds) == n_replicas, 'Seeds must be provided for all replicas'
        for k in range(n_replicas):
            self.sim.run(stop_time=stop_time, seeds=seeds[k], verbose=verbose)
            self.results.append(self.sim.dump_stats())
        return self.results

    def save(self, save_dir: str, add_timestamp: bool = True, timestamp_format: str ="%Y%m%d_%H%M%S"):
        save_dir = save_dir if save_dir.endswith('/') else save_dir + '/'
        filename = f'{save_dir}{self.experiment_name}_{datetime.now().strftime(timestamp_format)}.pickle' if add_timestamp else f'{save_dir}{self.experiment_name}.pickle'
        with open(filename, 'wb') as handle:
            pickle.dump(self.results, handle, protocol=pickle.HIGHEST_PROTOCOL)
