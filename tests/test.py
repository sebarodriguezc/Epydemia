#%%
import sys
sys.path.append('../')
import importlib
import spreadpy as sp
importlib.reload(sp)
import matplotlib.pyplot as plt
import time
import numpy as np


#%%
if __name__ == '__main__':
    sim = sp.AgentBasedSim()

    # Initialize model
    pop_size = 100
    stream_pop = sp.Stream(seed=10753)
    sim.initialize_population(
        how='proportion_file',
        population_size=pop_size,
        network_seed=1024,
        filename='../data/population.csv')

    stream = sp.Stream(seed=1023)
    # sim.population.add_attribute('w1', stream.rand(pop_size))
    # sim.population.add_attribute('w2',  stream.uniform(0, 1-sim.population['w1'], pop_size))
    # sim.population.add_attribute('w3',  stream.uniform(0, 1-sim.population['w1']-sim.population['w2'], pop_size))

    sim.population.add_attribute('w1', np.full(pop_size, 0.1))  # Susceptibility 
    sim.population.add_attribute('w2', np.full(pop_size, 0.1))  # Severity
    sim.population.add_attribute('w3', np.full(pop_size, 0.1))   # Subjective norm
    sim.population.add_attribute('w4', np.full(pop_size, 0.7))   # PBC

    sim.population.add_attribute('susceptibility',  np.full(pop_size, 0.35))
    sim.population.add_attribute('pbc',  np.full(pop_size, 0.2))

    # Create layers of network
    # sim.add_layer(layer_name='community', how='random', p=0.05)  # p=0.005)
    sim.add_layer(layer_name='community', how='random', n=pop_size, m=5)  # p=0.005)
    #sim.add_layer(layer_name='school', how='random', p=0.05)  # p=0.005)

    # Define disease
    sim.add_disease(sp.Covid, {'infection_prob': 0.05,
                              'initial_cases': [0, 2, 10, 15, 30]})

    # Interventions
    stream = sp.Stream(seed=1023)
    initial_masking = 0.2
    '''
    sim.add_intervention('masking', 3, func=lambda x: x,
                         args=stream.choice([0, 1],
                                            pop_size,
                                            p=(1-initial_masking, initial_masking)))
    for t in range(6, 150):
        sim.add_intervention('masking_behavior', t,
                             stream=stream)
    '''
    sim.add_intervention(sp.Masking, 3, func=lambda x: x,
                         args=stream.choice([0, 1],
                                            pop_size,
                                            p=(1-initial_masking, initial_masking)))
    for t in range(6, 150):
        sim.add_intervention(sp.MaskingBehavior, t,
                             stream=stream)
    sim.add_intervention(sp.Vaccination, 50, disease_name='covid',
                         target_func=sp.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)
    sim.add_intervention(sp.Vaccination, 55, disease_name='covid',
                         target_func=sp.vaccinate_age, stream=stream,
                         age_target=(50, 65), coverage=0.6)

    # Run model
    tm = time.time()
    sim.run(stop_time=365)  # Streams should be set when running the model
    print(time.time() - tm)

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
    import matplotlib.ticker as mtick

    fig, ax1 = plt.subplots()
    plt.ylim((0, 1))
    color = 'tab:blue'
    ax1.set_xlabel('Days')
    ax1.set_ylabel('Masking %', color=color)
    ax1.plot(sim.collector['masking']/pop_size, color=color, label='Masking')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.spines[['top']].set_visible(False)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    ax2.set_ylabel('Symptomatic cases', color=color)  # we already handled the x-label with ax1
    ax2.plot(sim.collector['Sy'], color=color)
    ax2.spines[['top']].set_visible(False)
    ax2.tick_params(axis='y', labelcolor=color)

    #%%
    import matplotlib.ticker as mtick

    fig, ax1 = plt.subplots()
    plt.ylim((0, 1))
    color = 'tab:blue'
    ax1.set_xlabel('Days')
    ax1.set_ylabel('Masking %', color=color)
    ax1.plot(sim.collector['masking']/pop_size, color=color, label='Masking')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.spines[['top']].set_visible(False)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:purple'
    ax2.set_ylabel('Hospitalized', color=color)  # we already handled the x-label with ax1
    ax2.plot(sim.collector['H'], color=color)
    ax2.spines[['top']].set_visible(False)
    ax2.tick_params(axis='y', labelcolor=color)

    #%%
    color_dict = {0: 'white', 1: 'orange', 2: 'red', 3: 'red', 4: 'red',
                  5: 'green', 6: 'purple', 7: 'k'}
    labels = ['Susceptible', 'Exposed', 'Infected', 'I', 'I',
              'Recovered', 'Hospitalized']
    colors = [color_dict[i] for i in sim.population['covid']['states']]

    fig, ax = plt.subplots(figsize=(10, 10))
    sim.population.plot_network(ax, 'community', layout='kk',
                                vertex_color=colors, vertex_size=0.5)  # TODO: #15 Plotting function should be part of sim object
    for i in [0, 1, 2, 5, 6]:
        ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
                   label=labels[i])
    plt.legend(fontsize=12, loc='best')

    # Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)


    # %%
    import matplotlib.pyplot as plt

    # w*Attitude + w*close_contact (up to 2 degrees?) + w*hospitalizations + w*PBC
    # masking must be updated each day and consider masking at the previous step.

    x = np.linspace(-1, 1, 100)
    y = 1 / (1 + np.exp(-10*(x-0.4)))
    plt.plot(x, y)





# %%
