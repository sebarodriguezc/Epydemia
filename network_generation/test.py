from layer_generator import synthetic_population
import igraph as ig

synthetic_population('./data/pop.csv',
                     500,
                     5624,
                     './data/household_size.csv',
                     './data/household.csv',
                     './data/schools_size.csv',
                     25,
                     './data/workplaces.csv',
                     0.002,
                     './')


g = ig.Graph.Read_GraphML('households')
ig.plot(g, vertex_size=5, edge_width=1)