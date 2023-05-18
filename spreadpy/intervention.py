from . import Event

class Intervention(Event):
    ''' docstring '''

    def __init__(self, time, simulator, func=None, args=None):
        super().__init__(time, simulator)
        self.model = simulator
        self.func = func
        self.args = args

    def do(self):
        pass


class Masking(Intervention):
    '''docstring'''

    def do(self):
        self.model.population['masking'] = self.func(self.args)
        # or self.model.population['masking'] = self.func(self.args)
        self.model.population.update_transmission_weights()


class Quarantine(Intervention):
    '''docstring'''

    def do(self):
        self.model.population['quarantine'] = self.func(self.args)
        # or self.model.population['masking'] = self.func(self.args)
        self.model.population.network.update_transmission_weights()


class Quarantine(Intervention):
    '''docstring'''

    def do(self):
        self.model.population['quarantine'] = self.func(self.args)
        # or self.model.population['masking'] = self.func(self.args)
        self.model.population.network.update_transmission_weights()