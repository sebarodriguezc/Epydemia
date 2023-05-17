#%%
from population import Population
from disease import Covid, ImportCases
import matplotlib.pyplot as plt
from simulator import AgentBasedSim, Step
from intervention import Masking
import time
from base import Stream

#%%
if __name__ == '__main__':
    stream = Stream(seed=1023)
    Covid.stream = Stream(seed=1054)
    import random #For igraph random
    random.seed(2904)


    sim = AgentBasedSim(Step)
    covid = Covid(sim,
                  {'infection_prob': 0.05})

    # Init population THIS MUST BE IMPLEMENTED ON A MODEL INIT FUNCTION.
    n = 1000
    average_contacts = 3
    pop = Population(n)
    pop.create_random_contact_layer(p=0.035, layer_name='community')
    # pop.create_random_contact_layer(p=0.02, layer_name='schools')
    # pop.create_random_contact_layer(p=0.05, layer_name='workplaces')
    pop.introduce_disease(covid)

    ImportCases(0, sim, pop, [0, 2, 10, 15, 30])

    # Interventions
    import numpy as np
    Masking(1, sim, lambda x: x, np.zeros(n))  # stream.randint(2, size=n))

    sim.set_population(pop)
    tm = time.time()
    sim.run(stop_time=365, step_length=1)  # Streams should be set when running the model
    tm = time.time() - tm
    print(tm)

    #%%
    import matplotlib.pyplot as plt
    plt.plot(sim.S, label='S')
    plt.plot(sim.E, label='E')
    plt.plot(sim.I, label='I')
    plt.plot(sim.R, label='R')
    plt.plot(sim.H, label='H')
    plt.plot(sim.D, label='D')
    plt.legend()


    #%% 
    import igraph as ig
    color_dict = {0: 'white', 1:'orange', 2: 'red', 3:'red', 4:'red',
                5: 'green', 6:'purple', 7:'k'}
    labels = ['Susceptible', 'Exposed', 'Infected', 'I', 'I',
              'Recovered', 'Hospitalized']
    colors = [color_dict[i] for i in sim.population['covid']['states']]
    #for i in [0, 2, 10, 15]:
    #    colors[i] = 'cyan'
    #layout = sim.population.network['community'].layout('kk')

    fig, ax = plt.subplots(figsize=(10, 10))
    sim.population.plot_network(ax, 'community')

    ig.plot(sim.population.network['community'], layout='kk',
            vertex_size=0.35, vertex_color=colors)#, target=ax)
    for i in [0, 1, 2, 5, 6]:
        ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
                   label=labels[i])
    plt.legend(fontsize=16, loc='upper right')
    plt.savefig('./img/network.png', bbox_inches='tight', dpi=1200)

### Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


# %%
