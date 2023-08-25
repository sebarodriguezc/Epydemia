from . import SubsObject
import numpy as np


class StatsCollector(SubsObject):

    def collect(self, stat_name, value):
        if stat_name not in self.attributes.keys():
            self[stat_name] = [value]
        else:
            self[stat_name].append(value)

    def clear(self):
        self.attributes = {}
