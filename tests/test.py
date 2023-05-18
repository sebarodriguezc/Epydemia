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
    stream = sp.Stream(seed=1023)

    sim = sp.AgentBasedSim(sp.Step)
    pop_size = 1000
    sim.initialize(population_size=pop_size)

    sim.add_layer(layer_name='community', how='random', p=0.035)
    
    # Define disease
    sim.add_disease('covid', {'infection_prob': 0.1})

    # Interventions
    sim.add_intervention('Masking', 1, func=lambda x: x, args=stream.randint(2, size=pop_size))

    sim.add_intervention('Masking', 100, func=lambda x: x, args=np.zeros(pop_size))

    # Run model
    sim.run(stop_time=365)  # Streams should be set when running the model

    #%%
    plt.plot(sim.S, label='S')
    plt.plot(sim.E, label='E')
    plt.plot(sim.I, label='I')
    plt.plot(sim.R, label='R')
    plt.plot(sim.H, label='H')
    plt.plot(sim.D, label='D')
    plt.legend()

    #%% 
    color_dict = {0: 'white', 1:'orange', 2: 'red', 3:'red', 4:'red',
                5: 'green', 6:'purple', 7:'k'}
    labels = ['Susceptible', 'Exposed', 'Infected', 'I', 'I',
              'Recovered', 'Hospitalized']
    colors = [color_dict[i] for i in sim.population['covid']['states']]

    fig, ax = plt.subplots(figsize=(10, 10))
    sim.population.plot_network(ax, 'community', layout='kk', vertex_color=colors,
                                vertex_size=0.5)
    for i in [0, 1, 2, 5, 6]:
        ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
                   label=labels[i])
    plt.legend(fontsize=16, loc='upper right')

### Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


# %%
