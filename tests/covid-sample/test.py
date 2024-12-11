#%%
import sys
sys.path.append('../../')
sys.path.append('/covid-sample/')
import importlib
import epydemia as epy
importlib.reload(epy)
import numpy as np
from covid import Covid, ImportCases
from interventions import Masking, MaskingBehavior, Vaccination
from step import DailyStep


#%%
if __name__ == '__main__':
    # Initialize model
    simulate_for = 20
    pop_size = 50

    sim = epy.AgentBasedSim(DailyStep)
    network = epy.Network(precompute_neighbors=True, seed=0)
    network.add_layer(layer_label='community', how='erdos_renyi', n=pop_size, p=0.05)
    sim.create_population(
        how='proportion_file',
        population_size=pop_size,
        network_seed=1024,
        population_seed=10753,
        filename='../../data/population.csv',
        network=network)

    # Behavioral parameters
    stream = epy.Stream(seed=3654)
    sim.population.add_attribute('w1', stream.rand(pop_size))   # Susceptibility 
    sim.population.add_attribute('w2', stream.uniform(0, 1 - sim.population['w1'], size=pop_size))   # Severity
    sim.population.add_attribute('w3', stream.uniform(0, 1 - sim.population['w1'] - sim.population['w2'], size=pop_size))  # Subjective norm
    sim.population.add_attribute('w4', 1 - sim.population['w1'] - sim.population['w2'] - sim.population['w3'])  # PBC
    sim.population.add_attribute('susceptibility',  np.full(pop_size, 0.2))
    sim.population.add_attribute('pbc',  stream.rand(pop_size))

    # Masking parameters
    sim.population.add_attribute('masking', np.zeros(pop_size))
    sim.population.add_attribute('vaccination', np.zeros(pop_size))

    # Define disease
    states = ['susceptible', 'exposed', 'presymptomatic', 'symptomatic',
              'asymptomatic', 'recovered', 'hospitalized', 'death']
    covid_seed = stream.choice(['susceptible', 'recovered'], size=pop_size, p=[1, 0])
    sim.add_disease(Covid, states_seed=covid_seed,
                    disease_kwargs={'infection_prob': 0.6,
                                    'initial_cases': 3,
                                    'states': states})

    # Interventions
    stream = epy.Stream(seed=1023)
    initial_masking = 0.2
    sim.add_intervention(Masking, 3, func=lambda x: x,
                         args=stream.choice([0, 1],
                                            pop_size,
                                            p=(1-initial_masking,
                                               initial_masking)))
    for t in range(6, simulate_for):
        sim.add_intervention(MaskingBehavior, t,
                             stream=stream)
    sim.add_intervention(Vaccination, 50, disease_name='covid',
                         target_func=epy.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)
    sim.add_intervention(Vaccination, 55, disease_name='covid',
                         target_func=epy.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)


    # Run model
    sim.run(stop_time=simulate_for, disease_random_seeds=[1323])




# %%
