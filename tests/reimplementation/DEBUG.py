#%%
import sys
sys.path.append('../../')
sys.path.append('/covid-sample/')
import importlib
import epydemia as epy
importlib.reload(epy)
import matplotlib.pyplot as plt
import time
import numpy as np
from covid import Covid, ImportCases
from interventions import Masking, MaskingBehavior, Vaccination
from step import DailyStep
from epydemia.basedesim import StreamsManager

#%%
if __name__ == '__main__':

    streams = StreamsManager(labels={'covid':1, 'util':3})

    sim = epy.AgentBasedSim(DailyStep, streams=streams)

    # Initialize model
    simulate_for = 5
    pop_size = 50
    sim.create_population(
        how='proportion_file',
        population_size=pop_size,
        network_seed=1024,
        population_seed=10753,
        filename='../../data/population.csv')

    # Masking parameters
    sim.population.add_attribute('masking', np.zeros(pop_size))
    sim.population.add_attribute('vaccination', np.zeros(pop_size))

    # Create layers of network
    sim.add_layer(layer_label='community', how='erdos_renyi', n=pop_size, p=0.05)

    # Define disease
    states = ['susceptible', 'exposed', 'presymptomatic', 'symptomatic',
              'asymptomatic', 'recovered', 'hospitalized', 'death']

    sim.add_disease(Covid,
                    initial_state=sim.streams['util'].choice(['susceptible', 'recovered'], size=pop_size, p=[1, 0]),
                    infection_prob=0.6, initial_cases=3, states=states)

    # Interventions
    initial_masking = 0.2
    sim.add_intervention(Masking, time=3, func=lambda x: x,
                         args=sim.streams['util'].choice([0, 1],
                                            pop_size,
                                            p=(1-initial_masking,
                                               initial_masking)))
    sim.add_intervention(Vaccination, time=50, disease_name='covid',
                         target_func=epy.vaccinate_age, stream=sim.streams['util'],
                         age_target=(50, 65), coverage=0.6)
    sim.add_intervention(Vaccination, time=55, disease_name='covid',
                         target_func=epy.vaccinate_age, stream=sim.streams['util'],
                         age_target=(50, 65), coverage=0.6)

    sim.run(stop_time=simulate_for, seeds={'covid':1323})

    print('running new\n\n\n\n')
    sim.run(stop_time=simulate_for, seeds={'covid':1323})

