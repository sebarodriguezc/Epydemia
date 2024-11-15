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

#%%
if __name__ == '__main__':
    sim = epy.AgentBasedSim(DailyStep)

    # Initialize model
    simulate_for = 20
    pop_size = 50
    sim.create_population(
        how='proportion_file',
        population_size=pop_size,
        network_seed=1024,
        population_seed=10753,
        filename='../../data/population.csv')

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

    # Create layers of network
    # sim.add_layer(layer_name='community', how='barabasi', n=pop_size, m=10)
    sim.add_layer(layer_label='community', how='erdos_renyi', n=pop_size, p=0.05)

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
    
    # Import cases
    #ImportCases(150, sim, 5)
    #ImportCases(250, sim, 5)

    # Run model
    tm = time.time()
    sim.run(stop_time=simulate_for, disease_random_seeds=[1323])
    print(time.time() - tm)

    #%%
    plt.plot(sim.collector['S'], label='S')
    plt.plot(sim.collector['E'], label='E')
    plt.plot(np.sum([sim.collector['Sy'], sim.collector['A'], sim.collector['P']], axis=0),
             label='I')
    plt.plot(sim.collector['R'], label='R')
    #plt.plot(sim.collector['H'], label='H')
    #plt.plot(sim.collector['D'], label='D')
    plt.xlabel('Days')
    plt.ylabel('# of agents')
    plt.legend()
    plt.show()

    #%%
    # import matplotlib.ticker as mtick
    #
    # fig, ax1 = plt.subplots()
    # plt.ylim((0, 1))
    # color = 'tab:blue'
    # ax1.set_xlabel('Days')
    # ax1.set_ylabel('Masking %', color=color)
    # ax1.plot(np.array(sim.collector['masking'])/pop_size, color=color, label='Masking')
    # ax1.tick_params(axis='y', labelcolor=color)
    # ax1.spines[['top']].set_visible(False)
    # ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    # ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    #
    # color = 'tab:red'
    # ax2.set_ylabel('Symptomatic cases', color=color)  # we already handled the x-label with ax1
    # ax2.plot(sim.collector['Sy'], color=color)
    # ax2.spines[['top']].set_visible(False)
    # ax2.tick_params(axis='y', labelcolor=color)
    #
    # #%%
    # import matplotlib.ticker as mtick
    #
    # fig, ax1 = plt.subplots()
    # plt.ylim((0, 1))
    # color = 'tab:blue'
    # ax1.set_xlabel('Days')
    # ax1.set_ylabel('Masking %', color=color)
    # ax1.plot(sim.collector['masking']/pop_size, color=color, label='Masking')
    # ax1.tick_params(axis='y', labelcolor=color)
    # ax1.spines[['top']].set_visible(False)
    # ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    # ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    #
    # color = 'tab:purple'
    # ax2.set_ylabel('Hospitalized', color=color)  # we already handled the x-label with ax1
    # ax2.plot(sim.collector['H'], color=color)
    # ax2.spines[['top']].set_visible(False)
    # ax2.tick_params(axis='y', labelcolor=color)
    #
    # #%%
    # color_dict = {0: 'white', 1: 'orange', 2: 'red', 3: 'red', 4: 'red',
    #               5: 'green', 6: 'purple', 7: 'k'}
    # labels = ['Susceptible', 'Exposed', 'Infected', 'I', 'I',
    #           'Recovered', 'Hospitalized']
    # colors = [color_dict[i] for i in sim.population['covid']]
    #
    #
    # fig, ax = plt.subplots(figsize=(10, 10))
    # sim.population.plot_network(ax, 'community', layout='kk',
    #                             vertex_color=colors, vertex_size=0.5)  # TODO: #15 Plotting function should be part of sim object
    # handles = ax.get_children()
    # for i in range(pop_size):
    #     center = handles[i].get_center()
    #     ax.text(center[0], center[1], str(i), ha='center', va='center')
    # for i in [0, 1, 2, 5, 6]:
    #     ax.scatter([], [], s=100, c=color_dict[i], edgecolor='gray',
    #                label=labels[i])
    # plt.legend(fontsize=12, loc='best')
    #
    # # Assign random weights. Then, prob of contagion is 1 - (1-p1)(1-p2)
    #
    #
    # # %%
    # import matplotlib.pyplot as plt
    #
    # # w*Attitude + w*close_contact (up to 2 degrees?) + w*hospitalizations + w*PBC
    # # masking must be updated each day and consider masking at the previous step.
    #
    # x = np.linspace(-1, 1, 100)
    # y = 1 / (1 + np.exp(-10*(x-0.4)))
    # plt.plot(x, y)
    #
    # # %%
    # from matplotlib.lines import Line2D
    #
    # fig, ax = plt.subplots(figsize=(10,10))
    # graph = sim.population.network['community'].graph
    # layout = graph.layout('kk')
    # color_dict = {0: 'white', 1: 'orange', 2: 'red', 3: 'red', 4: 'red',
    #               5: 'green', 6: 'purple', 7: 'k'}
    # colors = [[color_dict[i] for i in states] for states in sim.collector['states']]
    #
    # color_dict = {0: 'white', 1: 'orange', 2: 'red', 3: 'green'}
    # labels = ['Susceptible', 'Exposed', 'Infected', 'Recovered']
    #
    #
    # legend_elements = [
    #                 Line2D([0], [0], marker='o', color='w', label='Susceptible',
    #                         markerfacecolor='white', markeredgecolor='k', markersize=25),
    #                 Line2D([0], [0], marker='o', color='w', label='Exposed',
    #                         markerfacecolor='orange', markersize=25),
    #                 Line2D([0], [0], marker='o', color='w', label='Infected',
    #                         markerfacecolor='red', markersize=25),
    #                 Line2D([0], [0], marker='o', color='w', label='Recovered',
    #                         markerfacecolor='green', markersize=25)]
    # ax.legend(handles=legend_elements, loc='upper right', fontsize=20)
    # fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    #
    # plot_kwargs = {'edge_width': 0.3, 'vertex_size': 0.4}
    # epy.plot.animate(fig, ax, graph, colors, layout, save_as = 'ani.gif',
    #                 frames=simulate_for,
    #                 fps=1, interval=1000, plot_kwargs=plot_kwargs,
    #                 saving_kwargs={'savefig_kwargs': {'bbox_inches': 'tight'},
    #                                'dpi':300})
    #
    # for i in [0, 1, 2, 3]:
    #     ax.scatter([], [], s=100, c=color_dict[i], edgecolor='k',
    #                 label=labels[i])
    # plt.legend(fontsize=12, loc='best')

# %%
