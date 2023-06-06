#%%
import sys
sys.path.append('../')
#import os
#os.chdir('../')
import spreadpy as sp
import matplotlib.pyplot as plt
import time
import numpy as np


#%%
if __name__ == '__main__':
    sim = sp.AgentBasedSim()

    # Initialize model
    pop_size = 200
    stream_pop = sp.Stream(seed=10753)
    sim.initialize_population(
        how='proportion_file',
        population_size=pop_size,
        network_seed=1024,
        filename='../data/population.csv')

    # Create layers of network
    sim.add_layer(layer_name='community', how='random', p=0.05)  # p=0.005)
    sim.add_layer(layer_name='school', how='random', p=0.05)  # p=0.005)

    # Define disease
    sim.add_disease('covid', {'infection_prob': 0.15})

    # Interventions
    stream = sp.Stream(seed=1023)
    sim.add_intervention('masking', 7, func=lambda x: x,
                         args=stream.randint(2, size=pop_size))
    sim.add_intervention('masking', 60, func=lambda x: x,
                         args=np.zeros(pop_size))
    sim.add_intervention('vaccination', 50, disease_name='covid',
                         target_func=sp.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)
    sim.add_intervention('vaccination', 55, disease_name='covid',
                         target_func=sp.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)

    # Run model
    sim.run(stop_time=200)  # Streams should be set when running the model

    #%%
    plt.plot(sim.collector['S'], label='S')
    plt.plot(sim.collector['E'], label='E')
    plt.plot(sim.collector['Sy']+sim.collector['A']+sim.collector['P'],
             label='I')
    plt.plot(sim.collector['R'], label='R')
    plt.plot(sim.collector['H'], label='H')
    plt.plot(sim.collector['D'], label='D')
    plt.legend()

    #%%
    color_dict = {0: 'white', 1:'orange', 2: 'red', 3:'red', 4:'red',
                5: 'green', 6:'purple', 7:'k'}
    labels = ['Susceptible', 'Exposed', 'Infected', 'I', 'I',
              'Recovered', 'Hospitalized']
    colors = [color_dict[i] for i in sim.population['covid']['states']]

    fig, ax = plt.subplots(figsize=(10, 10))
    sim.population.plot_network(ax, 'school', layout='kk',
                                vertex_color=colors, vertex_size=0.5)  # TODO: #15 Plotting function should be part of sim object
    for i in [0, 1, 2, 5, 6]:
        ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
                   label=labels[i])
    plt.legend(fontsize=12, loc='best')

    # Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


# %%
