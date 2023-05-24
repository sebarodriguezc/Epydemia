#%%
import sys
sys.path.append('../')
#import os
#os.chdir('../')
import spreadpy as sp
import matplotlib.pyplot as plt
import time
import numpy as np

def vaccinate_age(population, stream, age_target, coverage):
    idx_ = np.where((population['age'] >= age_target[0]) &
                    (population['age'] <= age_target[1]))[0]
    return stream.choice(idx_, size=round(int(len(idx_)*coverage)),
                         replace=False)

#%%
if __name__ == '__main__':
    stream = sp.Stream(seed=1023)

    sim = sp.AgentBasedSim()
    pop_size = 1000

    # Initialize model
    sim.initialize_population(population_size=pop_size, network_seed=1024,
                              demographics_kwargs={'age_lims': (0, 65)},
                              demographics='random')
    # initialize population from census data?

    # Create layers of network
    sim.add_layer(layer_name='community', how='random', p=0.005)
    sim.add_layer(layer_name='school', how='random', p=0.005)

    # Define disease
    sim.add_disease('covid', {'infection_prob': 0.15})

    # Interventions
    sim.add_intervention('Masking', 1, func=lambda x: x, args=stream.randint(2, size=pop_size))
    sim.add_intervention('Masking', 100, func=lambda x: x, args=np.zeros(pop_size))
    sim.add_intervention('Vaccination', 50, disease_name='covid',
                         target_func=vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)
    sim.add_intervention('Vaccination', 55, disease_name='covid',
                         target_func=vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)


    # Run model
    sim.run(stop_time=100)  # Streams should be set when running the model

    #%%
    plt.plot(sim.collector['S'], label='S')
    plt.plot(sim.collector['E'], label='E')
    plt.plot(sim.collector['Sy']+sim.collector['A']+sim.collector['P'], label='I')
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
    sim.population.plot_network(ax, 'community', layout='kk', vertex_color=colors,
                            vertex_size=0.1)
    for i in [0, 1, 2, 5, 6]:
        ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
                   label=labels[i])
    plt.legend(fontsize=16, loc='upper right')

### Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


# %%
