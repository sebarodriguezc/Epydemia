from . import Event

# TODO: #14 Simulator must initialize the required attributes 'masking', 'quarantine'

class Intervention(Event):
    ''' docstring '''

    def __init__(self, time, simulator, **kwargs):
        # TODO: #13 Rethink how interventions are defined in terms of args
        super().__init__(time, simulator)
        self.simulator = simulator
        self.kwargs = kwargs

    def do(self):
        pass
