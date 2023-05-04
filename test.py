#%%
from population import Population
from disease import Covid, ImportCases
import matplotlib.pyplot as plt
from spredpy import AgentBasedSim, Step
import time

#%%
if __name__ == '__main__':

    sim = AgentBasedSim(Step)

    covid = Covid(sim,
        {'infection_prob': 0.2})

    # Init population THIS MUST BE IMPLEMENTED ON A MODEL INIT FUNCTION.
    n = 200
    average_contacts = 3
    pop = Population(n)
    pop.create_random_contact_layer(p=0.01, layer_name='community')
    #pop.create_random_contact_layer(p=0.02, layer_name='schools')
    #pop.create_random_contact_layer(p=0.05, layer_name='workplaces')
    pop.introduce_disease(covid)

    ImportCases(0, sim, pop, [0, 2, 10, 15, 30])
    #ImportCases(40, sim, pop, [2648, 3540, 30, 1520])

    sim.set_population(pop)
    sim.run(stop_time=10, step_length=1)
    
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
    color_dict = {0: 'blue', 1:'orange', 2: 'red', 3:'red', 4:'red',
                5: 'green', 6:'purple', 7:'k'}
    labels = ['S', 'E', 'I', 'I', 'I', 'R']
    colors = [color_dict[i] for i in sim.population['covid']['states']]
    #for i in [0, 2, 10, 15]:
    #    colors[i] = 'cyan'
    layout = sim.population.network['community'].layout('kk')

    fig, ax = plt.subplots(figsize=(5, 5))
    ig.plot(sim.population.network['community'], layout='kk',
            vertex_size=5, vertex_color=colors, ax=ax)
    #for i in range(6):
    #    ax.scatter([], [], c=color_dict[i], label=labels[i])
    #plt.legend()

### Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


# %%
